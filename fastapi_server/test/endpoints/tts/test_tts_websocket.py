import asyncio

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

from components.tts.websocket_handler import TTSQueue
from src.main import app


@pytest.fixture
def client():
    """Create a test client."""
    with TestClient(app) as c:
        yield c


class TestWebsocketEndpoint:
    @pytest.mark.asyncio
    async def test_ws_accepts_valid_connection(self, client):
        """Test that WebSocket accepts connection with valid stream/lang."""
        with patch("routes.tts_websocket.IRCClient") as mock_irc:
            mock_irc_instance = MagicMock()
            mock_irc_instance.connect = AsyncMock()
            mock_irc.return_value = mock_irc_instance
            mock_irc_instance.listen = AsyncMock()
            mock_irc_instance.shutdown = AsyncMock()

            with client.websocket_connect("/tts-api/ws/teststream/none"):
                assert TTSQueue.is_connected("teststream", "none") is True

    @pytest.mark.asyncio
    async def test_ws_rejects_invalid_lang(self, client):
        """Test that WebSocket rejects invalid read_name_lang."""
        with pytest.raises(Exception), client.websocket_connect("/tts-api/ws/teststream/invalid_lang"):
            pass

    @pytest.mark.asyncio
    async def test_ws_initializes_queue(self, client):
        """Test that first connection initializes the queue."""
        with patch("routes.tts_websocket.IRCClient") as mock_irc:
            mock_irc_instance = MagicMock()
            mock_irc_instance.connect = AsyncMock()
            mock_irc.return_value = mock_irc_instance
            mock_irc_instance.listen = AsyncMock()
            mock_irc_instance.shutdown = AsyncMock()

            assert TTSQueue.get_text_queue("newstream", "none") is None

            with client.websocket_connect("/tts-api/ws/newstream/none"):
                assert TTSQueue.get_text_queue("newstream", "none") is not None

    @pytest.mark.asyncio
    async def test_ws_removes_ws_on_disconnect(self, client):
        """Test that WebSocket is removed from queue on disconnect."""
        with patch("routes.tts_websocket.IRCClient") as mock_irc:
            mock_irc_instance = MagicMock()
            mock_irc_instance.connect = AsyncMock()
            mock_irc.return_value = mock_irc_instance
            mock_irc_instance.listen = AsyncMock()
            mock_irc_instance.shutdown = AsyncMock()

            with client.websocket_connect("/tts-api/ws/disconnectstream/none"):
                assert TTSQueue.is_connected("disconnectstream", "none") is True

            await asyncio.sleep(0.1)
            assert TTSQueue.is_connected("disconnectstream", "none") is False
