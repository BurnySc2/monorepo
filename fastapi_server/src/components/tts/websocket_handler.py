import asyncio
import base64
from dataclasses import dataclass, field
from datetime import timedelta
from typing import ClassVar, cast

import arrow
import orjson
from fastapi import WebSocket, WebSocketDisconnect
from loguru import logger
from websockets import ConnectionClosedError, ConnectionClosedOK

from components.tts.irc_bot_async import IRCClient, UserRole, UserRoles
from components.tts_generate import generate_audio, get_voice_by_label
from schemas.tts.engine import TTSEngine


@dataclass
class RoleFilter:
    allow_mods: bool = True
    allow_vips: bool = True
    allow_subs: bool = True
    allow_normal: bool = True

    def allows(self, roles: UserRole | UserRoles | set[UserRole]) -> bool:
        role_set = {roles} if isinstance(roles, str) else roles
        if "broadcaster" in role_set:
            return True
        if len(role_set) == 0:
            return self.allow_normal
        for role in role_set:
            if role == "mod" and self.allow_mods:
                return True
            if role == "vip" and self.allow_vips:
                return True
            if role == "sub" and self.allow_subs:
                return True
            if role == "normal" and self.allow_normal:
                return True
        return False


@dataclass
class TTSQueue:
    """
    Central coordination class for TTS WebSocket connections and text processing.

    Manages:
    - Text queues for each stream_name
    - Connected WebSocket clients for each stream
    - Twitch IRC bot connection state

    Provides methods to:
    - Add/remove WebSocket connections
    - Queue text for TTS processing
    - Check connection status
    - Manage IRC channel joins/parts

    Works with TTSQueueRunner which processes the queues and generates TTS audio.
    """

    # {stream_name: asyncio.Queue}
    # Each queue item is a tuple[voice: str, text: str, roles: UserRoles]
    text_queue: ClassVar[dict[str, asyncio.Queue]] = {}
    # {stream_name: {Websocket: RoleFilter}}
    connected_websockets: ClassVar[dict[str, dict[WebSocket, RoleFilter]]] = {}
    # {stream_name: irc_client}
    twitch_irc_bots: ClassVar[dict[str, IRCClient]] = {}

    @classmethod
    def irc_client_add_text_method(
        cls,
        stream_name: str,
        username: str,
        message: str,
        roles: UserRoles | UserRole = "normal",
    ):
        """Callback function for irc client on new message."""
        if isinstance(roles, str):
            roles = frozenset({roles})
        if stream_name.strip() == "":
            return
        if ":" not in message:
            return
        try:
            # engine_voice: text (voice lookup is case-insensitive, text preserves case)
            voice_label_raw, text_raw = message.split(":", maxsplit=1)
            voice_label = voice_label_raw.strip().lower()
            # engine name, voice name
            engine, voice_internal = voice_label.split("_", 1)
        except ValueError:
            # Not in the correct format
            return
        voice = get_voice_by_label(engine, voice_internal)
        if voice is None:
            return
        text = text_raw.strip()
        if text == "":
            # No text, just voice
            return
        sockets = cls.connected_websockets.get(stream_name)
        if sockets is None or not any(f.allows(roles) for f in sockets.values()):
            return
        queue = cls.text_queue.get(stream_name)
        if queue is None:
            return
        queue.put_nowait((f"{voice.engine}_{voice.label}", text, roles))

    @classmethod
    def add_websocket(cls, stream_name: str, socket: WebSocket, role_filter: RoleFilter | None = None) -> None:
        if stream_name not in cls.connected_websockets:
            cls.connected_websockets[stream_name] = {}
        if role_filter is None:
            role_filter = RoleFilter()
        cls.connected_websockets[stream_name][socket] = role_filter

    @classmethod
    def get_text_queue(cls, stream_name: str) -> asyncio.Queue | None:
        return cls.text_queue.get(stream_name, None)

    @classmethod
    def get_connected_websockets(cls, stream_name: str) -> dict[WebSocket, RoleFilter]:
        return cls.connected_websockets.get(stream_name, {})

    @classmethod
    def is_connected(cls, stream_name: str) -> bool:
        return stream_name in cls.connected_websockets

    @classmethod
    async def remove_ws(cls, socket: WebSocket, stream_name: str) -> None:
        connected_websockets: dict[WebSocket, RoleFilter] = cls.get_connected_websockets(stream_name)
        for ws in list(connected_websockets.keys()):
            if ws == socket:
                del connected_websockets[ws]
        # Remove dict entry if websockets-list is empty, which means no more websocket is connected.
        if len(connected_websockets) == 0:
            await cls.remove_websockets_key(stream_name)

    @classmethod
    async def remove_websockets_key(cls, stream_name: str) -> None:
        """
        Remove key from dictionaries
        Check if any websocket is connected to this stream channel
        Leave if none connected
        """
        # pop with default so double-cleanup or missing keys do not raise KeyError.
        cls.text_queue.pop(stream_name, None)
        cls.connected_websockets.pop(stream_name, None)
        # Shut down irc bot (close writer so listen() unblocks and exits)
        irc_client = cls.twitch_irc_bots.pop(stream_name, None)
        if irc_client is None:
            return
        try:
            await irc_client.shutdown()
        except Exception:  # noqa: BLE001
            logger.exception(f"IRC shutdown failed for {stream_name}")


@dataclass
class TTSQueueRunner:
    """
    Worker class that processes TTS requests for a specific stream.

    Responsibilities:
    - Continuously checks the text queue for new messages
    - Generates TTS audio via generate_tts()
    - Streams audio to all connected WebSocket clients
    - Manages timing between TTS segments
    - Cleans up when all clients disconnect

    Key behaviors:
    - Runs in an infinite loop until the queue is removed (no clients left)
    - Respects TTS playback duration (won't start new TTS while one is playing)
    - Handles WebSocket disconnections and errors gracefully
    - Logs TTS generation and delivery events

    Works in conjunction with TTSQueue which manages the shared state.
    """

    stream_name: str
    tts_is_playing_till: arrow.Arrow = field(default_factory=arrow.utcnow)

    @property
    def text_queue(self) -> asyncio.Queue[tuple[str, str, UserRoles]] | None:
        return TTSQueue.get_text_queue(self.stream_name)

    @property
    def text_queue_exists(self) -> bool:
        return TTSQueue.get_text_queue(self.stream_name) is not None

    @property
    def connected_websockets(self) -> dict[WebSocket, RoleFilter]:
        return TTSQueue.get_connected_websockets(self.stream_name)

    async def run(self):
        while True:
            # End worker if text queue was removed which means all connected websockets have disconnected
            if not self.text_queue_exists:
                return
            queue = self.text_queue
            if queue is None:
                return

            # TTS is still playing
            if arrow.utcnow() < self.tts_is_playing_till:
                await asyncio.sleep(0.1)
                continue

            # No new items
            if queue.empty():
                await asyncio.sleep(0.1)
                continue

            item = await queue.get()
            try:
                voice, text, roles = item
                targets = [ws for ws, f in self.connected_websockets.items() if f.allows(roles)]
                if not targets:
                    continue
                engine, internal_voice = voice.split("_", 1)
                logger.info(f"Generating tts: {self.stream_name}: ({voice}) {text}")

                # Generate audio from text
                try:
                    mp3_bytes, duration = await generate_audio(cast(TTSEngine, engine), internal_voice, text)
                except (RuntimeError, AssertionError) as e:
                    logger.error(e)
                    continue
            except Exception:  # noqa: BLE001
                logger.exception(f"TTS generation failed for {self.stream_name}")
                continue
            finally:
                queue.task_done()
            logger.info(f"Sending generated tts to clients: {self.stream_name}: ({voice}) {text}")
            # Fan-out to all clients (one failure must not cancel others).
            results = await asyncio.gather(
                *(self.send_mp3_data_to_ws(ws, base64.b64encode(mp3_bytes).decode()) for ws in list(targets)),
                return_exceptions=True,
            )
            for result in results:
                if isinstance(result, BaseException) and not isinstance(
                    result, (asyncio.CancelledError, ConnectionClosedError, ConnectionClosedOK, WebSocketDisconnect)
                ):
                    logger.exception(f"TTS fan-out failed: {result}")
            logger.info(f"Sent generated tts to clients: {self.stream_name}: ({voice}) {text}")

            self.tts_is_playing_till = arrow.utcnow() + timedelta(seconds=duration)

    async def send_mp3_data_to_ws(self, socket: WebSocket, data: str) -> None:
        """Send mp3 base64 data to frontend via WebSocket as JSON."""
        try:
            await socket.send_text(orjson.dumps({"data": data}).decode())
        # Catch errors and remove websocket on error
        except (ConnectionClosedError, ConnectionClosedOK, WebSocketDisconnect):
            await TTSQueue.remove_ws(socket, self.stream_name)
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Unexpected exception: {e}")
            await TTSQueue.remove_ws(socket, self.stream_name)
