"""
IRC Client Implementation for Twitch chat using asyncio
"""

import asyncio
import contextlib
import re
import ssl
import time
from collections.abc import Callable
from typing import Literal

from loguru import logger
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential, wait_random

# pyrefly: ignore
ALLOWED_NAME_LANGUAGES: dict[str, tuple[str | None, str | None]] = {
    # {str: (Voice label, suffix 'says')}
    "none": (None, None),
    "en": ("Narrator", "says"),
    "de": ("German Female", "sagt"),
}

# If no ping received by this time, reconnect
TWITCH_PING_TIMEOUT_SECONDS = 6 * 60  # Ping received roughly every 5mins
TIMEOUT_SECONDS = 60  # Timeout "readline()" after n seconds


ReadNameLang = Literal["none", "en", "de"]


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
        # Single bounded budget (outer max). Inner _connect_with_retry is only
        # 3 attempts, so worst case is 10 * 3 = 30 connects, not 1000 * 1000.
        self.max_reconnect_attempts = 10
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

        logger.info(f"Connected to {self.host}:{self.port} channel {self.channel} as {self.nick}")
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
                if self.reconnect_attempts >= self.max_reconnect_attempts:
                    # Break instead of spinning forever after budget is exhausted.
                    logger.error("IRC listen stopping: max reconnection attempts reached")
                    return
                if not self.reader or not self.writer:
                    await self.handle_reconnect()
                    # Back off to avoid tight reconnect loop.
                    await asyncio.sleep(1)
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
                    # wait_for timed out (TimeoutError suppressed) -> back off, do not spin.
                    await asyncio.sleep(1)
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
                    match = re.fullmatch(r":(\w+)!\w+@\w+\.tmi\.twitch\.tv PRIVMSG #\w+ :(.+)", message)
                    if match:
                        username, content = match.groups()
                        self.callback(self.channel, self.read_name_lang, username, content)

            except Exception as e:  # noqa: BLE001
                logger.exception(f"Error receiving message: {e}")
                await self.handle_reconnect()

    @retry(
        # Small inner budget only; outer handle_reconnect enforces the single
        # total budget via max_reconnect_attempts (10). Worst case 10 * 3 connects.
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=60) + wait_random(0, 1),
        retry=retry_if_exception_type((OSError, TimeoutError, ssl.SSLError, ConnectionError)),
        before_sleep=lambda retry_state: logger.info(f"Retrying IRC connect (attempt {retry_state.attempt_number})..."),
        reraise=True,
    )
    async def _connect_with_retry(self) -> None:
        """Connect with tenacity exponential backoff + jitter for transient network errors."""
        await self.connect()

    async def handle_reconnect(self):
        """Handle reconnection via tenacity-backed connect retry (single bounded budget)."""
        logger.info(f"Running reconnect to channel {self.channel}")
        if self.writer:
            self.writer.close()
            with contextlib.suppress(Exception):
                await self.writer.wait_closed()

        if self.reconnect_attempts >= self.max_reconnect_attempts:
            # Sleep once then break (caller listen() also breaks on max).
            logger.error("Max reconnection attempts reached")
            await asyncio.sleep(1)
            return

        self.reconnect_attempts += 1
        logger.info(
            f"Reconnecting to channel {self.channel} "
            f"(attempt {self.reconnect_attempts}/{self.max_reconnect_attempts})..."
        )

        try:
            await self._connect_with_retry()
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Reconnection failed: {e}")
            # Back off after failed budget slice to avoid tight loop.
            await asyncio.sleep(min(60, 2 ** min(self.reconnect_attempts, 6)))
            return
        # Guard: real connect() sets reader/writer. If still missing (e.g., mocked
        # connect in offline tests), yield to avoid a tight reconnect loop that would
        # starve the event loop. Real path never sleeps here.
        if not self.reader or not self.writer:
            await asyncio.sleep(1)

    async def shutdown(self):
        # Setting channel to empty-string ends listen(); close writer so
        # a blocked readline() unblocks and the listen task can exit promptly.
        self.channel = ""
        writer, self.writer = self.writer, None
        if writer is not None:
            with contextlib.suppress(Exception):
                writer.close()
                await writer.wait_closed()
        self.reader = None


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
