import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from components import tts_generate
from components.tts.websocket_handler import RoleFilter, TTSQueue
from schemas.tts import VoiceInfo


@pytest.fixture(autouse=True)
def _clean_tts_queue():
    TTSQueue.text_queue.clear()
    TTSQueue.connected_websockets.clear()
    TTSQueue.twitch_irc_bots.clear()
    yield
    TTSQueue.text_queue.clear()
    TTSQueue.connected_websockets.clear()
    TTSQueue.twitch_irc_bots.clear()


class TestAddWebsocket:
    def test_add_websocket(self):
        """Test adding a WebSocket to TTSQueue."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws)
        assert TTSQueue.get_connected_websockets("stream1") == {mock_ws: RoleFilter()}

    def test_add_websocket_multiple(self):
        """Test adding multiple WebSockets to the same stream."""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws1)
        TTSQueue.add_websocket("stream1", mock_ws2)
        assert len(TTSQueue.get_connected_websockets("stream1")) == 2

    def test_add_websocket_different_streams(self):
        """Test adding WebSockets to different streams."""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws1)
        TTSQueue.add_websocket("stream2", mock_ws2)
        assert TTSQueue.get_connected_websockets("stream1") == {mock_ws1: RoleFilter()}
        assert TTSQueue.get_connected_websockets("stream2") == {mock_ws2: RoleFilter()}


class TestRemoveWs:
    @pytest.mark.asyncio
    async def test_remove_ws(self):
        """Test removing a specific WebSocket."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws)
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        mock_irc = MagicMock()
        mock_irc.shutdown = AsyncMock()
        TTSQueue.twitch_irc_bots["stream1"] = mock_irc
        await TTSQueue.remove_ws(mock_ws, "stream1")
        assert TTSQueue.get_connected_websockets("stream1") == {}
        assert "stream1" not in TTSQueue.text_queue

    @pytest.mark.asyncio
    async def test_remove_ws_cleans_empty_key(self):
        """Test that removing the last WebSocket also cleans up the key."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws)
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        mock_irc = MagicMock()
        mock_irc.shutdown = AsyncMock()
        TTSQueue.twitch_irc_bots["stream1"] = mock_irc
        await TTSQueue.remove_ws(mock_ws, "stream1")
        assert "stream1" not in TTSQueue.connected_websockets
        assert "stream1" not in TTSQueue.text_queue

    @pytest.mark.asyncio
    async def test_remove_ws_preserves_other_websockets(self):
        """Test that removing one WebSocket preserves others."""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws1)
        TTSQueue.add_websocket("stream1", mock_ws2)
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        mock_irc = MagicMock()
        mock_irc.shutdown = AsyncMock()
        TTSQueue.twitch_irc_bots["stream1"] = mock_irc
        await TTSQueue.remove_ws(mock_ws1, "stream1")
        assert TTSQueue.get_connected_websockets("stream1") == {mock_ws2: RoleFilter()}
        assert "stream1" in TTSQueue.text_queue


class TestGetTextQueue:
    def test_get_text_queue_missing(self):
        """Test that get_text_queue returns None for non-existent key."""
        result = TTSQueue.get_text_queue("nonexistent")
        assert result is None

    def test_get_text_queue_exists(self):
        """Test that get_text_queue returns the queue for existing key."""
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        result = TTSQueue.get_text_queue("stream1")
        assert result is not None
        assert isinstance(result, asyncio.Queue)


class TestGetConnectedWebsockets:
    def test_get_connected_websockets_empty(self):
        """Test that get_connected_websockets returns empty list for missing key."""
        result = TTSQueue.get_connected_websockets("nonexistent")
        assert result == {}

    def test_get_connected_websockets_with_sockets(self):
        """Test that get_connected_websockets returns list of connected sockets."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws)
        result = TTSQueue.get_connected_websockets("stream1")
        assert result == {mock_ws: RoleFilter()}


class TestIsConnected:
    def test_is_connected_true(self):
        """Test is_connected returns True when WebSocket is connected."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws)
        assert TTSQueue.is_connected("stream1") is True

    def test_is_connected_false(self):
        """Test is_connected returns False when no WebSocket connected."""
        assert TTSQueue.is_connected("nonexistent") is False

    def test_is_connected_different_streams(self):
        """Test is_connected checks specific stream."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", mock_ws)
        assert TTSQueue.is_connected("stream1") is True
        assert TTSQueue.is_connected("stream2") is False


class TestIrcClientAddTextMethod:
    @pytest.fixture(autouse=True)
    def _seed_voice_cache(self):
        """Seed voice cache so irc_client_add_text_method can resolve voices hermetically."""
        original = dict(tts_generate._label_to_voice_info)
        tts_generate._label_to_voice_info.clear()
        tts_generate._label_to_voice_info.update(
            {
                ("tiktok", "narrator"): VoiceInfo(
                    engine="tiktok",
                    internal_name="en_male_narration",
                    label="Narrator",
                    gender="Male",
                    locale="en-us",
                ),
                ("tiktok", "german female"): VoiceInfo(
                    engine="tiktok",
                    internal_name="de_001",
                    label="German Female",
                    gender="Female",
                    locale="de-de",
                ),
            }
        )
        yield
        tts_generate._label_to_voice_info.clear()
        tts_generate._label_to_voice_info.update(original)

    def test_add_text_valid_voice(self):
        """Test parsing valid 'voice:text' message and adding to queue."""
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        TTSQueue.add_websocket("stream1", MagicMock())
        TTSQueue.irc_client_add_text_method("stream1", "user", "tiktok_narrator:Hello World")
        queue = TTSQueue.get_text_queue("stream1")
        assert queue is not None
        item = queue.get_nowait()
        assert item[0] == "tiktok_Narrator"
        assert item[1] == "Hello World"
        assert item[2] == frozenset({"normal"})

    def test_add_text_invalid_voice(self):
        """Test that invalid voice names are ignored."""
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        TTSQueue.add_websocket("stream1", MagicMock())
        TTSQueue.irc_client_add_text_method("stream1", "user", "INVALID_VOICE:Hello World")
        queue = TTSQueue.get_text_queue("stream1")
        assert queue is not None
        assert queue.empty()

    def test_add_text_empty_message(self):
        """Test that empty messages after voice are ignored."""
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        TTSQueue.add_websocket("stream1", MagicMock())
        TTSQueue.irc_client_add_text_method("stream1", "user", "tiktok_narrator:")
        queue = TTSQueue.get_text_queue("stream1")
        assert queue is not None
        assert queue.empty()

    def test_add_text_no_prefix_single_item(self):
        """Test that no username prefix is added and only a single item is queued."""
        TTSQueue.text_queue["stream1"] = asyncio.Queue()
        TTSQueue.add_websocket("stream1", MagicMock())
        TTSQueue.irc_client_add_text_method("stream1", "testuser", "tiktok_narrator:Hello World")
        queue = TTSQueue.get_text_queue("stream1")
        assert queue is not None
        item = queue.get_nowait()
        assert item[1] == "Hello World"
        assert item[2] == frozenset({"normal"})
        assert queue.empty()
