import asyncio
from dataclasses import dataclass, field
from datetime import timedelta
from typing import ClassVar, Literal

import arrow
from litestar import WebSocket
from litestar.exceptions.websocket_exceptions import WebSocketDisconnect
from litestar.handlers import WebsocketListener
from loguru import logger
from websockets import ConnectionClosedError, ConnectionClosedOK

from routes.tts.generate_tts import Voices, generate_tts
from routes.tts.irc_bot_async import ALLOWED_NAME_LANGUAGES, AsyncIrcBot

VOICE_NAMES_LOWERCASE: set[str] = {voice.name.lower() for voice in Voices}


@dataclass
class TTSQueue:
    # {stream_name: {read_name_lang: asyncio.Queue}}
    text_queue: ClassVar[dict[tuple[str, str], asyncio.Queue]] = {}
    # {stream_name: {read_name_lang: list[Websocket]}}
    connected_websockets: ClassVar[dict[tuple[str, str], list[WebSocket]]] = {}
    joined_twitch_channels: ClassVar[set[str]] = set()
    twitch_irc_bot: ClassVar[AsyncIrcBot | None] = None

    @classmethod
    def add_websocket(cls, stream_name: str, read_name_lang: str, socket: WebSocket) -> None:
        if (stream_name, read_name_lang) not in cls.connected_websockets:
            cls.connected_websockets[(stream_name, read_name_lang)] = []
        cls.connected_websockets[(stream_name, read_name_lang)].append(socket)

    @classmethod
    async def add_text_queue(cls, stream_name: str, read_name_lang: str, voice: Voices, text: str) -> None:
        if (stream_name, read_name_lang) not in cls.text_queue:
            cls.text_queue[(stream_name, read_name_lang)] = asyncio.Queue()
        if text == "":
            return
        await cls.text_queue[(stream_name, read_name_lang)].put((voice, text))

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

        # Leave irc channel if no websocket is connected
        if not cls.is_connected(stream_name):
            logger.info(f"Disconnecting from irc channel: {stream_name}")
            cls.joined_twitch_channels.discard(stream_name)
            assert TTSQueue.twitch_irc_bot is not None
            await TTSQueue.twitch_irc_bot.part([f"#{stream_name}"])

    @classmethod
    async def start_irc_bot(cls) -> None:
        cls.twitch_irc_bot = AsyncIrcBot(tts_queue=TTSQueue)
        await cls.twitch_irc_bot.connect()


@dataclass
class TTSQueueRunner:
    """
    Worker waits for currently running tts to finish before queueing a new one.
    Wait for newly queued text to arrive to be converted to audio and played on all connected websockets.
    End endless loop if there are no more connected websockets.
    """

    stream_name: str
    read_name_lang: str
    tts_is_playing_till: arrow.Arrow = field(default_factory=arrow.utcnow)

    @property
    def text_queue(self) -> asyncio.Queue | None:
        return TTSQueue.get_text_queue(self.stream_name, self.read_name_lang)

    @property
    def text_queue_exists(self) -> bool:
        return TTSQueue.get_text_queue(self.stream_name, self.read_name_lang) is not None

    @property
    def connected_websockets(self) -> list[WebSocket]:
        return TTSQueue.get_connected_websockets(self.stream_name, self.read_name_lang)

    async def run(self):
        await TTSQueue.add_text_queue(self.stream_name, self.read_name_lang, Voices.STORY_TELLER, text="")
        while 1:
            # End worker if text queue was removed which means all connected websockets have disconnected
            if not self.text_queue_exists:
                return

            # TTS is still playing
            if arrow.utcnow() < self.tts_is_playing_till:
                await asyncio.sleep(0.1)
                continue

            # No new items
            if self.text_queue.empty():
                await asyncio.sleep(0.1)
                continue

            # Generate tts
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
            self.text_queue.task_done()
            tasks = [
                asyncio.create_task(
                    self.send_template_to_ws(
                        ws,
                        f"""
                    <div hx-swap-oob="innerHTML:#content">
                        <audio controls autoplay id="audio">
                            <source src="data:audio/mpeg;base64, { mp3_b64_data }" type="audio/mpeg" />
                            Your browser does not support the audio element.
                        </audio>
                    </div>
                    """,
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

    async def on_accept(self, socket: WebSocket, stream_name: str, read_name_lang: Literal["none", "en", "de"]) -> None:
        """
        On new ws-connection:
            - join twitch channel
            - create worker that checks for new items in queue
        """
        # Is this required?
        await socket.accept(headers={"Cookie": "custom-cookie"})

        # Add socket
        TTSQueue.add_websocket(stream_name, read_name_lang, socket)
        if (stream_name, read_name_lang) not in TTSQueue.text_queue:
            # Create worker for this 'stream_name' and 'read_name_lang'
            asyncio.create_task(TTSQueueRunner(stream_name, read_name_lang).run())

        # Join twitch channel
        assert TTSQueue.twitch_irc_bot is not None
        await TTSQueue.twitch_irc_bot.wait_till_ready()
        if stream_name not in TTSQueue.joined_twitch_channels:
            logger.info(f"Connecting to irc channel: {stream_name}")
            assert TTSQueue.twitch_irc_bot is not None
            await TTSQueue.twitch_irc_bot.join([f"#{stream_name}"])
            TTSQueue.joined_twitch_channels.add(stream_name)

    async def on_disconnect(
        self, socket: WebSocket, stream_name: str, read_name_lang: Literal["none", "en", "de"]
    ) -> None:
        await TTSQueue.remove_ws(socket, stream_name, read_name_lang)

    async def on_receive(self, data: str, stream_name: str) -> str:  # pyre-fixme[14]
        return ""
