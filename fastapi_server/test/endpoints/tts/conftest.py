import pytest

from components.tts.websocket_handler import TTSQueue


@pytest.fixture(autouse=True)
def reset_tts_queue():
    """Reset TTSQueue class variables before each test to avoid cross-test contamination."""
    TTSQueue.text_queue.clear()
    TTSQueue.connected_websockets.clear()
    TTSQueue.twitch_irc_bots.clear()
    yield
    TTSQueue.text_queue.clear()
    TTSQueue.connected_websockets.clear()
    TTSQueue.twitch_irc_bots.clear()
