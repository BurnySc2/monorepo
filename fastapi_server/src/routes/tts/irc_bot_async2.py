"""
IRC Client Implementation for Twitch chat using asyncio

TODO:
4. Testing Requirements:
   - External test file: test/endpoints/tts/test_irc_bot.py
   - Mock IRC server for testing
   - Test connection/reconnection scenarios
   - Verify message parsing and callback invocation
"""

import asyncio
import contextlib
import re
import ssl
import time
from collections.abc import Callable
from typing import Literal

from loguru import logger

from routes.tts.generate_tts import Voices

# pyrefly: ignore
VOICE_NAMES_LOWERCASE: set[str] = {voice.name.lower() for voice in Voices}

# pyrefly: ignore
ALLOWED_NAME_LANGUAGES: dict[str, tuple[Voices | None, str | None]] = {
    # {str: (Voice, suffix 'says')}
    "none": (None, None),
    "en": (Voices.STORY_TELLER, "says"),
    "de": (Voices.GERMAN_FEMALE, "sagt"),
}

# If no ping received by this time, reconnect
TWITCH_PING_TIMEOUT_SECONDS = 6 * 60  # Ping received roughly every 5mins
TIMEOUT_SECONDS = 60  # Timeout "readline()" after n seconds

type ReadNameLang = Literal["none", "en", "de"]


class IRCClient:
    def __init__(
        self,
        channel: str,
        read_name_lang: ReadNameLang,
        callback: Callable[[str, ReadNameLang, str, str], None],
    ):
        """
        Callback params:
        - stream_name
        - read_name_lang: Literal['none', 'de', 'en']
        - voice: one valid Voice
        - text: str
        """
        self.host = "irc.chat.twitch.tv"  # Use standard IRC endpoint
        self.port = 6697  # Standard IRC SSL port
        self.nick = "justinfan12345"
        self.channel = channel
        self.read_name_lang = read_name_lang
        self.callback = callback
        self.reader: asyncio.StreamReader | None = None
        self.writer: asyncio.StreamWriter | None = None
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 1000
        self.last_ping = 0.0

    async def connect(self):
        """Connect to IRC server and join channel"""
        ssl_context = ssl.create_default_context()
        self.reader, self.writer = await asyncio.open_connection(self.host, self.port, ssl=ssl_context)

        # Send auth and join
        self.writer.write(f"USER {self.nick} :This is a fun bot!\r\n".encode())
        self.writer.write(f"NICK {self.nick}\r\n".encode())  # sets nick
        self.writer.write(b"PRIVMSG nickserv :iNOOPE\r\n")  # auth
        self.writer.write(f"JOIN #{self.channel}\r\n".encode())  # join channel
        await self.writer.drain()

        logger.info(f"Connected to {self.host}:{self.port} as {self.nick}")
        self.reconnect_attempts = 0
        self.last_ping = time.time()

    async def wait_till_ready(self) -> None:
        while not self.reader or not self.writer:
            await asyncio.sleep(1)

    async def listen(self):
        """Listen for incoming messages"""
        while True:
            try:
                if self.channel == "":
                    # shutdown() was called
                    return
                if not self.reader or not self.writer:
                    await self.handle_reconnect()
                    continue

                data = None
                # Wait for new chat message, timeout after n seconds
                with contextlib.suppress(TimeoutError):
                    data = await asyncio.wait_for(self.reader.readline(), timeout=TIMEOUT_SECONDS)
                    if not data:
                        logger.info("Reconnecting because no data was received")
                        await self.handle_reconnect()
                        continue

                if TWITCH_PING_TIMEOUT_SECONDS < time.time() - self.last_ping:
                    logger.info("Reconnecting because ping was ages ago")
                    await self.handle_reconnect()
                    continue

                if data is None:
                    continue
                message = data.decode().strip()
                if message.startswith("PING"):
                    # Handle ping
                    self.last_ping = time.time()
                    logger.info("Received PING")
                    self.writer.write(f"PONG {message[5:]}\r\n".encode())
                    await self.writer.drain()
                elif "PRIVMSG" in message:
                    # Extract username and message content
                    match = re.match(r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)", message)
                    if match:
                        username, content = match.groups()
                        self.callback(self.channel, self.read_name_lang, username, content)

            except Exception as e:  # noqa: BLE001
                logger.error(f"Error receiving message: {e}")
                await self.handle_reconnect()

    async def handle_reconnect(self):
        """Handle reconnection with exponential backoff"""
        logger.info(f"Running reconnect to channel {self.channel}")
        if self.writer:
            self.writer.close()
            with contextlib.suppress(Exception):
                await self.writer.wait_closed()

        if self.reconnect_attempts >= self.max_reconnect_attempts:
            logger.error("Max reconnection attempts reached")
            return

        delay = min(2**self.reconnect_attempts, 60)  # Max 60s delay
        self.reconnect_attempts += 1
        logger.info(f"Reconnecting in {delay} seconds...")
        await asyncio.sleep(delay)

        try:
            await self.connect()
        except Exception as e:  # noqa: BLE001
            logger.error(f"Reconnection failed: {e}")

    async def shutdown(self):
        # Setting channel to empty-string will end the for-loop
        self.channel = ""


async def main():
    """Main function to start the IRC client"""
    client = IRCClient(
        channel="burnysc2",
        read_name_lang="none",
        callback=lambda channel, read_name_lang, user, msg: logger.info(f"{channel} {user}: {msg}"),
    )
    await client.connect()
    await client.listen()


if __name__ == "__main__":
    asyncio.run(main())
