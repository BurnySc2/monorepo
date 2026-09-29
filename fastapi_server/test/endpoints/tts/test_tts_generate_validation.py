"""Gate3 critical tests for TTS generate validation ordering.

Malformed voice / unknown engine must return 400 without calling
_ensure_nltk_data; the valid path must call it exactly once.
"""

import base64
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from routes.tts_generate import TTSGenerateRequest, generate_tts


@pytest.mark.asyncio
async def test_malformed_voice_returns_400_without_calling_ensure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Voice without engine prefix returns 400 and skips NLTK ensure."""
    mock_ensure = MagicMock()
    mock_generate = AsyncMock()
    monkeypatch.setattr("routes.tts_generate.ensure_nltk_data", mock_ensure)
    monkeypatch.setattr("routes.tts_generate.generate_audio", mock_generate)

    with pytest.raises(HTTPException) as exc_info:
        await generate_tts(TTSGenerateRequest(voice="nounderscore", text="Hello"))

    assert exc_info.value.status_code == 400
    assert mock_ensure.call_count == 0
    assert mock_generate.call_count == 0


@pytest.mark.asyncio
async def test_unknown_engine_returns_400_without_calling_ensure(monkeypatch: pytest.MonkeyPatch) -> None:
    """Unknown engine returns 400 and skips NLTK ensure."""
    mock_ensure = MagicMock()
    mock_generate = AsyncMock()
    monkeypatch.setattr("routes.tts_generate.ensure_nltk_data", mock_ensure)
    monkeypatch.setattr("routes.tts_generate.generate_audio", mock_generate)

    with pytest.raises(HTTPException) as exc_info:
        await generate_tts(TTSGenerateRequest(voice="unknown_somevoice", text="Hello"))

    assert exc_info.value.status_code == 400
    assert mock_ensure.call_count == 0
    assert mock_generate.call_count == 0


@pytest.mark.asyncio
async def test_valid_path_calls_ensure_once(monkeypatch: pytest.MonkeyPatch) -> None:
    """Valid voice calls NLTK ensure exactly once before generating audio."""
    mock_ensure = MagicMock()
    mock_generate = AsyncMock(return_value=(b"fake-audio", 1.5))
    monkeypatch.setattr("routes.tts_generate.ensure_nltk_data", mock_ensure)
    monkeypatch.setattr("routes.tts_generate.generate_audio", mock_generate)

    result = await generate_tts(TTSGenerateRequest(voice="edge_test-voice", text="Hello world"))

    assert mock_ensure.call_count == 1
    assert mock_generate.call_count == 1
    assert base64.b64decode(result["audio_b64"]) == b"fake-audio"
    assert result["duration"] == 1.5
