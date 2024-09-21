import asyncio
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from httpx_ws import AsyncWebSocketSession, aconnect_ws
from loguru import logger

from routes.tts.generate_tts import Voices

if TYPE_CHECKING:
    from routes.tts.websocket_handler import TTSQueue

VOICE_NAMES_LOWERCASE: set[str] = {voice.name.lower() for voice in Voices}

ALLOWED_NAME_LANGUAGES: dict[str, tuple[Voices | None, str | None]] = {
    # {str: (Voice, suffix 'says')}
    "none": (None, None),
    "en": (Voices.STORY_TELLER, "says"),
    "de": (Voices.GERMAN_FEMALE, "sagt"),
}


@dataclass
class AsyncIrcBot:
    is_ready: bool = False
    username: str = "justinfan12345"
    host: str = "wss://irc-ws.chat.twitch.tv:443"
    ws: AsyncWebSocketSession | None = None  # Set in connect()
    tts_queue: type["TTSQueue"] | None = None

    async def connect(self):
        async with aconnect_ws(self.host) as ws:
            self.ws = ws
            await self.ws.send_text(f"USER {self.username} :This is a fun bot!")
            await self.ws.send_text(f"NICK {self.username}")  # sets nick
            await self.ws.send_text("PRIVMSG nickserv :iNOOPE")  # auth
            task = asyncio.create_task(self.receive())
            self.is_ready = True
            await asyncio.gather(task)

    async def wait_till_ready(self):
        while not self.is_ready:
            await asyncio.sleep(0.1)

    async def receive(self):
        while 1:
            messages = await self.ws.receive_text()
            logger.info(messages)
            message: str
            for message in messages.split("\r\n"):
                if message.strip() == "":
                    continue
                elif message.startswith("PING"):
                    await self.handle_ping(message)
                else:
                    await self.handle_message(message)
            await asyncio.sleep(0.01)

    async def join(self, channel_names: list[str]):
        """May be called multiple times."""
        assert all(channel.startswith("#") for channel in channel_names), channel_names
        channels_str = ",".join(channel_names)
        assert self.ws is not None
        await self.ws.send_text(f"JOIN {channels_str}")

    async def part(self, channel_names: list[str]):
        assert all(channel.startswith("#") for channel in channel_names), channel_names
        channels_str = ",".join(channel_names)
        assert self.ws is not None
        await self.ws.send_text(f"PART {channels_str}")

    async def handle_ping(self, message: str):
        if message == "PING :tmi.twitch.tv":
            assert self.ws is not None
            await self.ws.send_text("PONG :tmi.twitch.tv")

    async def handle_message(self, message: str):
        # Example message:
        # :burnysc2!burnysc2@burnysc2.tmi.twitch.tv PRIVMSG #burnysc2 :PING
        regex_display_name = ":(.+)!.*"
        regex_message_operation = "PRIVMSG"
        regex_channel_name = "#(.+)"
        regex_message_content = ":(.+)"
        regex_pattern = f"{regex_display_name} {regex_message_operation} {regex_channel_name} {regex_message_content}"

        regex_match = re.match(regex_pattern, message.strip())
        if regex_match is None:
            return
        display_name, channel_name, message_content = regex_match.groups()
        if message_content.endswith("\U000e0000"):
            message_content = message_content[:-1].strip()

        # === GENERATE TTS

        # Get and select voice
        voice_from_chat = message_content.lower().split(":")[0].strip()
        if voice_from_chat not in VOICE_NAMES_LOWERCASE:
            return
        selected_voice: Voices | None = None
        for voice in Voices:
            if voice.name.lower() == voice_from_chat:
                selected_voice = voice
                break
        # Voice could not be found
        if selected_voice is None:
            return

        text_from_chat_list = message_content.split(":")[1:]
        text_from_chat = ":".join(text_from_chat_list).strip()

        # Put voice and text into queue

        for read_name_lang, (voice, name_suffix) in ALLOWED_NAME_LANGUAGES.items():
            assert self.tts_queue is not None
            if self.tts_queue.is_connected(channel_name, read_name_lang):
                if voice is not None:
                    # Put "burnysc2 says:"
                    # logger.info(f"{read_name_lang} {voice} {name_suffix}")
                    assert self.tts_queue is not None
                    await self.tts_queue.add_text_queue(
                        channel_name, read_name_lang, voice, f"{display_name} {name_suffix}:"
                    )

                # Put text into queue
                logger.info(f"{channel_name}: {read_name_lang} says: {text_from_chat}")
                assert self.tts_queue is not None
                await self.tts_queue.add_text_queue(channel_name, read_name_lang, selected_voice, text_from_chat)


async def main_simple_example():
    async with aconnect_ws("wss://irc-ws.chat.twitch.tv:443") as ws:
        await ws.send_text("USER justinfan12345 :This is a fun bot!")
        await ws.send_text("NICK justinfan12345")  # sets nick
        await ws.send_text("PRIVMSG nickserv :iNOOPE")  # auth
        await ws.send_text("JOIN #burnysc2")  # join the chan
        while 1:
            message = await ws.receive_text()
            logger.info(message)
            await asyncio.sleep(0.1)


async def main():
    bot = AsyncIrcBot()
    task = asyncio.create_task(bot.connect())
    await bot.wait_till_ready()
    await bot.join(["#burnysc2"])
    # Keep websocket connection running
    await asyncio.gather(task)


if __name__ == "__main__":
    asyncio.run(main())
    # asyncio.run(main_simple_example())
