import asyncio
import json
from contextlib import suppress

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from components.tts.generate_tts import Voices
from components.tts.websocket_handler import TTSQueue, TTSQueueRunner


class TestTTSQueueRunnerRun:
    @pytest.mark.asyncio
    async def test_run_exits_when_queue_removed(self):
        """Test that worker exits when text queue no longer exists."""
        runner = TTSQueueRunner("stream1", "none")
        runner.run()
        await asyncio.sleep(0.05)
        assert runner.text_queue_exists is False

    @pytest.mark.asyncio
    async def test_run_waits_when_empty(self):
        """Test that worker sleeps when queue is empty."""
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        runner = TTSQueueRunner("stream1", "none")

        async def run_and_cancel():
            runner.run()

        task = asyncio.create_task(run_and_cancel())
        await asyncio.sleep(0.05)
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task

    @pytest.mark.asyncio
    async def test_run_processes_item(self):
        """Test that worker generates TTS and sends to WebSocket."""
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock()
        TTSQueue.add_websocket("stream1", "none", mock_ws)

        runner = TTSQueueRunner("stream1", "none")

        mock_b64_data = "test_base64_data"
        with patch("components.tts.websocket_handler.generate_tts", new_callable=AsyncMock) as mock_generate:
            mock_generate.return_value = (mock_b64_data, 1.0)
            TTSQueue.text_queue[("stream1", "none")].put_nowait((Voices.STORY_TELLER, "Hello"))

            async def run_task():
                await runner.run()

            task = asyncio.create_task(run_task())
            await asyncio.sleep(0.1)
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

            mock_generate.assert_called_once_with(Voices.STORY_TELLER, "Hello")

            sent_data = json.loads(mock_ws.send_text.call_args[0][0])
            assert sent_data["data"] == mock_b64_data


class TestSendMp3DataToWs:
    @pytest.mark.asyncio
    async def test_send_mp3_data_to_ws(self):
        """Test sending mp3 base64 data as JSON."""
        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock()
        runner = TTSQueueRunner("stream1", "none")

        await runner.send_mp3_data_to_ws(mock_ws, "test_base64")

        mock_ws.send_text.assert_called_once_with('{"data": "test_base64"}')

    @pytest.mark.asyncio
    async def test_send_mp3_data_removes_ws_on_disconnect(self):
        """Test that WebSocket is removed on disconnect."""
        from websockets import ConnectionClosedError

        mock_ws = MagicMock()
        mock_ws.send_text = AsyncMock(side_effect=ConnectionClosedError(None, None))
        runner = TTSQueueRunner("stream1", "none")
        TTSQueue.add_websocket("stream1", "none", mock_ws)
        TTSQueue.text_queue[("stream1", "none")] = asyncio.Queue()
        mock_irc = MagicMock()
        mock_irc.shutdown = AsyncMock()
        TTSQueue.twitch_irc_bots[("stream1", "none")] = mock_irc

        await runner.send_mp3_data_to_ws(mock_ws, "test_base64")

        assert mock_ws not in TTSQueue.get_connected_websockets("stream1", "none")
