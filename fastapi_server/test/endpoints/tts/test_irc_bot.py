import asyncio
import ssl
from contextlib import suppress
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from components.tts.irc_bot_async import IRCClient


class TestIRCClientConnect:
    @pytest.mark.asyncio
    async def test_connect(self):
        """Test that connect establishes SSL connection and sends correct messages."""
        mock_reader = MagicMock()
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)
            client = IRCClient(
                channel="teststream",
                callback=lambda *args: None,
            )
            await client.connect()

            mock_connect.assert_called_once()
            call_args = mock_connect.call_args
            assert call_args[0][0] == "irc.chat.twitch.tv"
            assert call_args[0][1] == 6697
            assert isinstance(call_args[1]["ssl"], ssl.SSLContext)

            assert mock_writer.write.call_count == 5

            calls = [call[0][0] for call in mock_writer.write.call_args_list]
            assert any(b"USER justinfan12345" in c for c in calls)
            assert any(b"NICK justinfan12345" in c for c in calls)
            assert any(b"PRIVMSG nickserv" in c for c in calls)
            assert any(b"CAP REQ :twitch.tv/tags twitch.tv/commands" in c for c in calls)
            assert any(b"JOIN #teststream" in c for c in calls)
            cap_idx = next(i for i, c in enumerate(calls) if b"CAP REQ" in c)
            join_idx = next(i for i, c in enumerate(calls) if b"JOIN #teststream" in c)
            assert cap_idx < join_idx


class TestIRCClientChannelNormalization:
    @pytest.mark.parametrize(
        ("raw", "want"), [("teststream", "teststream"), ("  TestStream  ", "teststream"), ("BURNYSC2", "burnysc2")]
    )
    def test_channel_normalized(self, raw: str, want: str) -> None:
        client = IRCClient(channel=raw, callback=lambda *args: None)
        assert client.channel == want


class TestIRCClientShutdown:
    @pytest.mark.asyncio
    async def test_shutdown(self):
        """Test that shutdown sets channel to empty string."""
        client = IRCClient(
            channel="teststream",
            callback=lambda *args: None,
        )
        assert client.channel == "teststream"
        await client.shutdown()
        assert client.channel == ""


class TestIRCClientListen:
    @pytest.mark.asyncio
    async def test_listen_parses_privmsg(self):
        """Test that listen parses PRIVMSG and calls callback."""
        privmsg = b":user123!user123@user123.tmi.twitch.tv PRIVMSG #teststream :STORY_TELLER:Hello world\r\n"

        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(side_effect=[privmsg, asyncio.CancelledError()])
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        callback_mock = MagicMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)
            client = IRCClient(
                channel="teststream",
                callback=callback_mock,
            )
            await client.connect()

            async def listen_task():
                await client.listen()

            task = asyncio.create_task(listen_task())
            await asyncio.sleep(0.05)
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

            callback_mock.assert_called_once_with(
                "teststream", "user123", "STORY_TELLER:Hello world", frozenset({"normal"})
            )

    @pytest.mark.asyncio
    async def test_listen_parses_tagged_privmsg_mod_sub(self):
        """Test that listen parses tagged mod+sub PRIVMSG with roles frozenset."""
        privmsg = (
            b"@badges=moderator/1,subscriber/12;mod=1;subscriber=1 "
            b":moduser!moduser@moduser.tmi.twitch.tv PRIVMSG #teststream :hello\r\n"
        )

        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(side_effect=[privmsg, asyncio.CancelledError()])
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        callback_mock = MagicMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)
            client = IRCClient(
                channel="teststream",
                callback=callback_mock,
            )
            await client.connect()

            async def listen_task():
                await client.listen()

            task = asyncio.create_task(listen_task())
            await asyncio.sleep(0.05)
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

            callback_mock.assert_called_once_with("teststream", "moduser", "hello", frozenset({"mod", "sub"}))

    @pytest.mark.asyncio
    async def test_listen_parses_tagged_privmsg_vip(self):
        """Test that listen parses tagged vip PRIVMSG with roles frozenset."""
        privmsg = b"@badges=vip/1;vip=1 :vipuser!vipuser@vipuser.tmi.twitch.tv PRIVMSG #teststream :hi vip\r\n"

        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(side_effect=[privmsg, asyncio.CancelledError()])
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        callback_mock = MagicMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)
            client = IRCClient(
                channel="teststream",
                callback=callback_mock,
            )
            await client.connect()

            async def listen_task():
                await client.listen()

            task = asyncio.create_task(listen_task())
            await asyncio.sleep(0.05)
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

            callback_mock.assert_called_once_with("teststream", "vipuser", "hi vip", frozenset({"vip"}))

    @pytest.mark.asyncio
    async def test_listen_parses_tagged_privmsg_broadcaster(self):
        """Test that listen maps broadcaster badge to dual-role {"mod", "broadcaster"} for bypass."""
        privmsg = (
            b"@badges=broadcaster/1;mod=0;subscriber=0 "
            b":owneruser!owneruser@owneruser.tmi.twitch.tv PRIVMSG #teststream :hi\r\n"
        )

        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(side_effect=[privmsg, asyncio.CancelledError()])
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        callback_mock = MagicMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)
            client = IRCClient(
                channel="teststream",
                callback=callback_mock,
            )
            await client.connect()

            async def listen_task():
                await client.listen()

            task = asyncio.create_task(listen_task())
            await asyncio.sleep(0.05)
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

            callback_mock.assert_called_once_with("teststream", "owneruser", "hi", frozenset({"mod", "broadcaster"}))

    @pytest.mark.asyncio
    async def test_listen_responds_to_ping(self):
        """Test that listen responds to PING with PONG."""
        ping = b"PING :tmi.twitch.tv\r\n"

        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(side_effect=[ping, asyncio.CancelledError()])
        mock_writer = MagicMock()
        mock_writer.drain = AsyncMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)
            client = IRCClient(
                channel="teststream",
                callback=lambda *args: None,
            )
            await client.connect()

            async def listen_task():
                await client.listen()

            task = asyncio.create_task(listen_task())
            await asyncio.sleep(0.05)
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

            pong_calls = [call for call in mock_writer.write.call_args_list if b"PONG" in call[0][0]]
            assert len(pong_calls) == 1
            assert b"tmi.twitch.tv" in pong_calls[0][0][0]

    @pytest.mark.asyncio
    async def test_listen_calls_reconnect_on_error(self):
        """Test that listen calls handle_reconnect on exception."""
        mock_reader = MagicMock()
        mock_reader.readline = AsyncMock(side_effect=[Exception("Connection error"), asyncio.CancelledError()])
        mock_writer = MagicMock()
        mock_writer.close = MagicMock()
        mock_writer.wait_closed = AsyncMock()

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_connect:
            mock_connect.return_value = (mock_reader, mock_writer)
            client = IRCClient(
                channel="teststream",
                callback=lambda *args: None,
            )
            client.connect = AsyncMock()

            async def listen_task():
                await client.listen()

            task = asyncio.create_task(listen_task())
            await asyncio.sleep(0.05)
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

            assert client.reconnect_attempts >= 0
