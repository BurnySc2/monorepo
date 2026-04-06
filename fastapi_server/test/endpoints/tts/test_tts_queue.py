import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from components.tts.generate_tts import Voices
from components.tts.websocket_handler import TTSQueue


class TestAddWebsocket:
    def test_add_websocket(self):
        """Test adding a WebSocket to TTSQueue."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws)
        assert TTSQueue.get_connected_websockets("stream1", "none") == [mock_ws]

    def test_add_websocket_multiple(self):
        """Test adding multiple WebSockets to the same stream."""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws1)
        TTSQueue.add_websocket("stream1", "none", mock_ws2)
        assert len(TTSQueue.get_connected_websockets("stream1", "none")) == 2

    def test_add_websocket_different_streams(self):
        """Test adding WebSockets to different stream/lang combinations."""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws1)
        TTSQueue.add_websocket("stream2", "none", mock_ws2)
        assert TTSQueue.get_connected_websockets("stream1", "none") == [mock_ws1]
        assert TTSQueue.get_connected_websockets("stream2", "none") == [mock_ws2]


class TestRemoveWs:
    @pytest.mark.asyncio
    async def test_remove_ws(self):
        """Test removing a specific WebSocket."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws)
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        mock_irc = MagicMock()
        mock_irc.shutdown = AsyncMock()
        TTSQueue.twitch_irc_bots[("stream1", "none")] = mock_irc
        await TTSQueue.remove_ws(mock_ws, "stream1", "none")
        assert TTSQueue.get_connected_websockets("stream1", "none") == []
        assert ("stream1", "none") not in TTSQueue.text_queue

    @pytest.mark.asyncio
    async def test_remove_ws_cleans_empty_key(self):
        """Test that removing the last WebSocket also cleans up the key."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws)
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        mock_irc = MagicMock()
        mock_irc.shutdown = AsyncMock()
        TTSQueue.twitch_irc_bots[("stream1", "none")] = mock_irc
        await TTSQueue.remove_ws(mock_ws, "stream1", "none")
        assert ("stream1", "none") not in TTSQueue.connected_websockets
        assert ("stream1", "none") not in TTSQueue.text_queue

    @pytest.mark.asyncio
    async def test_remove_ws_preserves_other_websockets(self):
        """Test that removing one WebSocket preserves others."""
        mock_ws1 = MagicMock()
        mock_ws2 = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws1)
        TTSQueue.add_websocket("stream1", "none", mock_ws2)
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        mock_irc = MagicMock()
        mock_irc.shutdown = AsyncMock()
        TTSQueue.twitch_irc_bots[("stream1", "none")] = mock_irc
        await TTSQueue.remove_ws(mock_ws1, "stream1", "none")
        assert TTSQueue.get_connected_websockets("stream1", "none") == [mock_ws2]
        assert ("stream1", "none") in TTSQueue.text_queue


class TestGetTextQueue:
    def test_get_text_queue_missing(self):
        """Test that get_text_queue returns None for non-existent key."""
        result = TTSQueue.get_text_queue("nonexistent", "none")
        assert result is None

    def test_get_text_queue_exists(self):
        """Test that get_text_queue returns the queue for existing key."""
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        result = TTSQueue.get_text_queue("stream1", "none")
        assert result is not None
        assert isinstance(result, asyncio.Queue)


class TestGetConnectedWebsockets:
    def test_get_connected_websockets_empty(self):
        """Test that get_connected_websockets returns empty list for missing key."""
        result = TTSQueue.get_connected_websockets("nonexistent", "none")
        assert result == []

    def test_get_connected_websockets_with_sockets(self):
        """Test that get_connected_websockets returns list of connected sockets."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws)
        result = TTSQueue.get_connected_websockets("stream1", "none")
        assert result == [mock_ws]


class TestIsConnected:
    def test_is_connected_true(self):
        """Test is_connected returns True when WebSocket is connected."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws)
        assert TTSQueue.is_connected("stream1", "none") is True

    def test_is_connected_false(self):
        """Test is_connected returns False when no WebSocket connected."""
        assert TTSQueue.is_connected("nonexistent", "none") is False

    def test_is_connected_with_specific_lang(self):
        """Test is_connected checks specific language."""
        mock_ws = MagicMock()
        TTSQueue.add_websocket("stream1", "en", mock_ws)
        assert TTSQueue.is_connected("stream1", "en") is True
        assert TTSQueue.is_connected("stream1", "de") is False


class TestIrcClientAddTextMethod:
    def test_add_text_valid_voice(self):
        """Test parsing valid 'voice:text' message and adding to queue."""
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        TTSQueue.irc_client_add_text_method("stream1", "none", "user", "STORY_TELLER:Hello world")
        queue = TTSQueue.get_text_queue("stream1", "none")
        assert queue is not None
        item = queue.get_nowait()
        assert item[0] == Voices.STORY_TELLER
        assert item[1] == "Hello world"

    def test_add_text_invalid_voice(self):
        """Test that invalid voice names are ignored."""
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        TTSQueue.irc_client_add_text_method("stream1", "none", "user", "INVALID_VOICE:Hello world")
        queue = TTSQueue.get_text_queue("stream1", "none")
        assert queue is not None
        assert queue.empty()

    def test_add_text_empty_message(self):
        """Test that empty messages after voice are ignored."""
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        TTSQueue.irc_client_add_text_method("stream1", "none", "user", "STORY_TELLER:")
        queue = TTSQueue.get_text_queue("stream1", "none")
        assert queue is not None
        assert queue.empty()

    def test_add_text_with_lang_prefix_en(self):
        """Test that username prefix is added for English language."""
        TTSQueue.text_queue[("stream1", "en")] = asyncio.Queue()
        TTSQueue.irc_client_add_text_method("stream1", "en", "testuser", "STORY_TELLER:Hello")
        queue = TTSQueue.get_text_queue("stream1", "en")
        assert queue is not None
        item1 = queue.get_nowait()
        assert item1[1] == "testuser says"
        item2 = queue.get_nowait()
        assert item2[1] == "Hello"

    def test_add_text_with_lang_prefix_de(self):
        """Test that username prefix is added for German language."""
        TTSQueue.text_queue[("stream1", "de")] = asyncio.Queue()
        TTSQueue.irc_client_add_text_method("stream1", "de", "testuser", "GERMAN_FEMALE:Hallo")
        queue = TTSQueue.get_text_queue("stream1", "de")
        assert queue is not None
        item1 = queue.get_nowait()
        assert item1[1] == "testuser sagt"
        item2 = queue.get_nowait()
        assert item2[1] == "Hallo"

    def test_add_text_with_lang_none(self):
        """Test that no prefix is added when lang is 'none'."""
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        TTSQueue.irc_client_add_text_method("stream1", "none", "testuser", "STORY_TELLER:Hello")
        queue = TTSQueue.get_text_queue("stream1", "none")
        assert queue is not None
        item = queue.get_nowait()
        assert item[1] == "Hello"
        assert queue.empty()
