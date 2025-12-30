import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import ClassVar, Literal

import arrow
from litestar import WebSocket
from litestar.exceptions.websocket_exceptions import WebSocketDisconnect
from litestar.handlers import WebsocketListener
from loguru import logger
from routes.tts.generate_tts import Voices, generate_tts
from routes.tts.irc_bot_async2 import ALLOWED_NAME_LANGUAGES, IRCClient, ReadNameLang
from websockets import ConnectionClosedError, ConnectionClosedOK

# pyrefly: ignore
VOICE_NAMES_LOWERCASE: set[str] = {voice.name.lower() for voice in Voices}


@dataclass
class TTSQueue:
    """
    Central coordination class for TTS WebSocket connections and text processing.

    Manages:
    - Text queues for each (stream_name, read_name_lang) combination
    - Connected WebSocket clients for each stream/language pair
    - Twitch IRC bot connection state

    Provides methods to:
    - Add/remove WebSocket connections
    - Queue text for TTS processing
    - Check connection status
    - Manage IRC channel joins/parts

    Works with TTSQueueRunner which processes the queues and generates TTS audio.
    """

    # {(stream_name, read_name_lang): asyncio.Queue}
    # Each queue item is a tuple[voice: str, text: str]
    text_queue: ClassVar[dict[tuple[str, str], asyncio.Queue]] = {}
    # {(stream_name, read_name_lang): list[Websocket]}
    connected_websockets: ClassVar[dict[tuple[str, str], list[WebSocket]]] = {}
    # {(stream_name, read_name_lang): irc_client}
    twitch_irc_bots: ClassVar[dict[tuple[str, str], IRCClient]] = {}

    @classmethod
    def irc_client_add_text_method(cls, stream_name: str, read_name_lang: ReadNameLang, username: str, message: str):
        """Callback function for irc client on new message."""
        # Sanity check: has voice in message
        message_lowercase = message.lower()
        if ":" in message_lowercase:
            message_voice, *content = message_lowercase.split(":")
            if message_voice not in VOICE_NAMES_LOWERCASE:
                return

        # Find voice name
        voice: Voices | None = None
        loop_voice: Voices
        for loop_voice in Voices.__iter__():
            if message_lowercase.startswith(f"{loop_voice.name.lower()}:"):
                voice = loop_voice
                break
        if voice is None:
            # No voice found
            return
        message = message[len(voice.name) + 1 :].strip()
        if message == "":
            # Message is empty
            return
        if read_name_lang != "none":
            username_says_voice, username_says_text = ALLOWED_NAME_LANGUAGES[read_name_lang]
            cls.text_queue[(stream_name, read_name_lang)].put_nowait(
                (username_says_voice, f"{username} {username_says_text}")
            )
        cls.text_queue[(stream_name, read_name_lang)].put_nowait((voice, message))

    @classmethod
    def add_websocket(cls, stream_name: str, read_name_lang: str, socket: WebSocket) -> None:
        if (stream_name, read_name_lang) not in cls.connected_websockets:
            cls.connected_websockets[(stream_name, read_name_lang)] = []
        cls.connected_websockets[(stream_name, read_name_lang)].append(socket)

    @classmethod
    def get_text_queue(cls, stream_name: str, read_name_lang: str) -> asyncio.Queue | None:
        return cls.text_queue.get((stream_name, read_name_lang), None)

    @classmethod
    def get_connected_websockets(cls, stream_name: str, read_name_lang: str) -> list[WebSocket]:
        return cls.connected_websockets.get((stream_name, read_name_lang), [])

    @classmethod
    def is_connected(cls, stream_name: str, read_name_lang: str | None = None) -> bool:
        """
        Check if connected to "stream_name" via given "read_name_lang".
        If "read_name_lang" is not given, check if connected to "stream_name" at all.
        """
        if read_name_lang is None:
            for read_name_lang_loop in ALLOWED_NAME_LANGUAGES:
                if cls.is_connected(stream_name, read_name_lang_loop):
                    return True
        return (stream_name, read_name_lang) in cls.connected_websockets

    @classmethod
    async def remove_ws(cls, socket: WebSocket, stream_name: str, read_name_lang: str) -> None:
        connected_websockets: list[WebSocket] = cls.get_connected_websockets(stream_name, read_name_lang)
        for ws in list(connected_websockets):
            if ws == socket:
                connected_websockets.remove(socket)
        # Remove dict entry if websockets-list is empty, which means no more websocket is connected.
        if len(connected_websockets) == 0:
            await cls.remove_websockets_key(stream_name, read_name_lang)

    @classmethod
    async def remove_websockets_key(cls, stream_name: str, read_name_lang: str) -> None:
        """
        Remove key from dictionaries
        Check if any websocket is connected to this stream channel
        Leave if none connected
        """
        cls.text_queue.pop((stream_name, read_name_lang))
        cls.connected_websockets.pop((stream_name, read_name_lang))
        # Shut down irc bot
        irc_client = cls.twitch_irc_bots.pop((stream_name, read_name_lang))
        await irc_client.shutdown()


@dataclass
class TTSQueueRunner:
    """
    Worker class that processes TTS requests for a specific stream/language pair.

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
    read_name_lang: str
    tts_is_playing_till: arrow.Arrow = field(default_factory=arrow.utcnow)

    @property
    def text_queue(self) -> asyncio.Queue[tuple[Voices, str]] | None:
        return TTSQueue.get_text_queue(self.stream_name, self.read_name_lang)

    @property
    def text_queue_exists(self) -> bool:
        return TTSQueue.get_text_queue(self.stream_name, self.read_name_lang) is not None

    @property
    def connected_websockets(self) -> list[WebSocket]:
        return TTSQueue.get_connected_websockets(self.stream_name, self.read_name_lang)

    async def run(self):
        while True:
            # End worker if text queue was removed which means all connected websockets have disconnected
            if not self.text_queue_exists:
                return

            # TTS is still playing
            if arrow.utcnow() < self.tts_is_playing_till:
                await asyncio.sleep(0.1)
                continue

            # No new items
            # pyrefly: ignore
            if self.text_queue.empty():
                await asyncio.sleep(0.1)
                continue

            # Generate tts
            # pyrefly: ignore
            voice, text = await self.text_queue.get()
            logger.info(f"Generating tts: {self.stream_name}: ({voice}) {text}")

            # Generate audio from text
            try:
                # TODO Intercept: tiktok session key api thing missing
                mp3_b64_data, duration = await generate_tts(voice, text)
            # logger.info(f"{duration}s: {text}")
            except AssertionError as e:
                logger.error(e)
                continue
            logger.info(f"Sending generated tts to clients: {self.stream_name}: ({voice}) {text}")
            # pyrefly: ignore
            self.text_queue.task_done()
            tasks = [
                asyncio.create_task(
                    self.send_template_to_ws(
                        ws,
                        f"""
<div hx-swap-oob="innerHTML:#content">
    <audio controls autoplay id="audio">
        <source src="data:audio/mpeg;base64, {mp3_b64_data}" type="audio/mpeg" />
        Your browser does not support the audio element.
    </audio>
</div>
                        """.strip(),
                    )
                )
                for ws in self.connected_websockets
            ]
            for task in asyncio.as_completed(tasks):
                await task
            logger.info(f"Sent generated tts to clients: {self.stream_name}: ({voice}) {text}")

            self.tts_is_playing_till = arrow.utcnow() + timedelta(seconds=duration)

    async def send_template_to_ws(self, socket: WebSocket, html: str) -> None:
        """Send the audio template to frontend. If socked closed/has error, catch it and remove websocket from list."""
        try:
            await socket.send_text(html)
        # Catch errors and remove websocket on error
        except (ConnectionClosedError, ConnectionClosedOK, WebSocketDisconnect):
            await TTSQueue.remove_ws(socket, self.stream_name, self.read_name_lang)
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Unexpected exception: {e}")
            await TTSQueue.remove_ws(socket, self.stream_name, self.read_name_lang)


class TTSWebsocketHandler(WebsocketListener):
    path = "/tts-ws/{stream_name: str}/{read_name_lang: str}"

    # pyrefly: ignore
    async def on_accept(self, socket: WebSocket, stream_name: str, read_name_lang: ReadNameLang) -> None:
        """
        On new ws-connection:
            - join twitch channel
            - create worker that checks for new items in queue
        """
        # Is this required?
        await socket.accept(headers={"Cookie": "custom-cookie"})

        # Initialize text queue if not exists
        if (stream_name, read_name_lang) not in TTSQueue.text_queue:
            TTSQueue.text_queue[(stream_name, read_name_lang)] = asyncio.Queue()
            # Create worker for this 'stream_name' and 'read_name_lang'
            asyncio.create_task(TTSQueueRunner(stream_name, read_name_lang).run())

        # Add socket - needs to happen after text_queue is initialized
        TTSQueue.add_websocket(stream_name, read_name_lang, socket)

        # Start irc bot: listen to messages in channel
        if (stream_name, read_name_lang) not in TTSQueue.twitch_irc_bots:
            new_irc_client = IRCClient(
                channel=stream_name, read_name_lang=read_name_lang, callback=TTSQueue.irc_client_add_text_method
            )
            TTSQueue.twitch_irc_bots[(stream_name, read_name_lang)] = new_irc_client
            await new_irc_client.connect()
            # Keep irc bot running
            asyncio.create_task(new_irc_client.listen())

    # pyrefly: ignore
    async def on_disconnect(
        self, socket: WebSocket, stream_name: str, read_name_lang: Literal["none", "en", "de"]
    ) -> None:
        await TTSQueue.remove_ws(socket, stream_name, read_name_lang)

    # pyrefly: ignore
    async def on_receive(self, data: str, stream_name: str) -> str:
        return ""
