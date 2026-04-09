"""Parametrized tests for individual TTS engines."""

from __future__ import annotations

import io
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydub.generators import Sine

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from components.tts_generate import ENGINES, generate_audio, list_voices

# Default voices for each engine
DEFAULT_VOICES = {
    "edge": "en-US-AriaNeural",
    "kokoro": "af_bella",
    "kitten": "Bella",
    "pocket": "alba",
    "supertonic": "F1",
    "tiktok": "en_us_002",
}


# Cloud engines that need mocking for generation tests
CLOUD_ENGINES = ["edge", "tiktok"]


def _make_minimal_mp3():
    """Create a minimal valid MP3 file using pydub."""
    sine = Sine(440).to_audio_segment(duration=100)
    mp3_io = io.BytesIO()
    sine.export(mp3_io, format="mp3")
    return mp3_io.getvalue()


class MockCommunicate:
    """Mock edge_tts.Communicate object."""

    def __init__(self, text, voice):
        self.text = text
        self.voice = voice
        self.duration = 1.5

    async def stream(self):
        yield {"data": _make_minimal_mp3()}

    async def save(self, output_path):
        Path(output_path).write_bytes(_make_minimal_mp3())

    async def get_audio(self, audio_obj):
        if hasattr(audio_obj, "duration"):
            audio_obj.duration = 1.5


@pytest.fixture
def mock_edge_tts():
    """Mock edge_tts module for testing."""
    with patch("edge_tts.Communicate", MockCommunicate):
        yield


@pytest.fixture
def mock_tiktok_httpx():
    """Mock httpx for TikTok TTS testing."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake_audio_data"

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_response
    mock_client.__aenter__.return_value = mock_client
    mock_client.__aexit__.return_value = None

    with patch("httpx.AsyncClient", return_value=mock_client):
        yield mock_client


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_list_voices_returns_non_empty_list(engine):
    """Each engine should return a non-empty list of voices."""
    voices = await list_voices(engine)
    assert isinstance(voices, list)
    assert len(voices) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_voices_have_name_attribute(engine):
    """Each voice should have a non-empty name."""
    voices = await list_voices(engine)
    for voice in voices:
        assert hasattr(voice, "name")
        assert isinstance(voice.name, str)
        assert len(voice.name) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_first_voice_is_valid(engine):
    """The first voice should be valid and usable."""
    voices = await list_voices(engine)
    first_voice = voices[0]
    assert first_voice.name


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_list_voices_idempotent(engine):
    """Calling list_voices multiple times should return consistent results."""
    voices1 = await list_voices(engine)
    voices2 = await list_voices(engine)
    assert len(voices1) == len(voices2)
    names1 = [v.name for v in voices1]
    names2 = [v.name for v in voices2]
    assert names1 == names2


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_with_default_voice(engine, mock_edge_tts, mock_tiktok_httpx):
    """Each engine should generate audio with its default voice."""
    text = "Hello, this is a test."

    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        audio_bytes, duration = await generate_audio(engine, voice, text)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
        assert duration > 0
    except OSError as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_creates_mp3_file(engine, mock_edge_tts, mock_tiktok_httpx):
    """Generated file should be a valid MP3 with positive size."""
    text = "Testing audio file creation."
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        audio_bytes, _ = await generate_audio(engine, voice, text)

        assert len(audio_bytes) > 0

        header = audio_bytes[:4]
        assert header[:3] == b"ID3" or header[0] == 0xFF
    except OSError as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_returns_positive_duration(engine, mock_edge_tts, mock_tiktok_httpx):
    """Generated audio should have a positive duration."""
    text = "Hello world testing duration."
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        _, duration = await generate_audio(engine, voice, text)
        assert duration > 0
        assert isinstance(duration, (int, float))
    except OSError as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_with_different_text_lengths(engine, mock_edge_tts, mock_tiktok_httpx):
    """Each engine should handle different text lengths."""
    texts = [
        "Short.",
        "Medium length text here.",
        "This is a much longer text that contains multiple sentences "
        "and should test how the engine handles longer inputs.",
    ]
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        for text in texts:
            audio_bytes, duration = await generate_audio(engine, voice, text)
            assert isinstance(audio_bytes, bytes)
            assert len(audio_bytes) > 0
            assert duration > 0
    except OSError as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_returns_bytes(engine, mock_edge_tts, mock_tiktok_httpx):
    """generate_audio should return bytes."""
    text = "Testing audio return."
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        audio_bytes, duration = await generate_audio(engine, voice, text)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
        assert duration > 0
    except OSError as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_list_voices_contains_string_names(engine):
    """Voice names should be strings."""
    voices = await list_voices(engine)
    for voice in voices:
        assert isinstance(voice.name, str)
        # Voice names should typically not be empty
        assert len(voice.name.strip()) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_engine_lowercase_handling(engine):
    """Engine name should be case-insensitive."""
    voices_lower = await list_voices(engine.lower())
    voices_upper = await list_voices(engine.upper())
    assert len(voices_lower) == len(voices_upper)
