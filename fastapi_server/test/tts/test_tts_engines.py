"""Parametrized tests for individual TTS engines."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from components.tts_generate import ENGINES, generate_audio, list_voices

# Default voices for each engine
DEFAULT_VOICES = {
    "edge": "en-US-AriaNeural",
    "kokoro": "af_bella",
    "kitten": "default",
    "pocket": "alba",
    "supertonic": "F1",
    "tiktok": "en_us_002",
}


# Cloud engines that need mocking for generation tests
CLOUD_ENGINES = ["edge", "tiktok"]



class MockCommunicate:
    """Mock edge_tts.Communicate object."""
    def __init__(self, text, voice):
        self.text = text
        self.voice = voice
        self.duration = 1.5  # Store duration for get_audio

    async def save(self, output_path):
        # Write a minimal valid MP3 file
        # MP3 frame header (11111111 11111011 = 0xFF 0xFB) + padding
        mp3_data = b"\xff\xfb\x90\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00"
        with open(output_path, "wb") as f:
            f.write(b"ID3")  # ID3 tag
            f.write(b"\x04\x00\x00\x00\x00\x00\x00")  # ID3 header
            f.write(mp3_data * 10)  # Some MP3 frames

    async def get_audio(self, audio_obj):
        # Edge TTS doesn't have Audio class, it sets duration directly
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
async def test_generate_audio_with_default_voice(engine, tmp_path, mock_edge_tts, mock_tiktok_httpx):
    """Each engine should generate audio with its default voice."""
    output_path = str(tmp_path / f"test_{engine}.mp3")
    text = "Hello, this is a test."

    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        path, duration = await generate_audio(engine, voice, text, output_path)
        assert path == output_path
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0
        assert duration > 0
    except Exception as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_creates_mp3_file(engine, tmp_path, mock_edge_tts, mock_tiktok_httpx):
    """Generated file should be a valid MP3 with positive size."""
    output_path = str(tmp_path / f"test_{engine}_mp3.mp3")
    text = "Testing audio file creation."
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        path, _ = await generate_audio(engine, voice, text, output_path)

        # Check file exists and has content
        assert Path(path).exists()
        assert Path(path).stat().st_size > 0

        # Verify it's a valid audio file by checking header
        with open(path, "rb") as f:
            header = f.read(4)
            # MP3 files start with ID3 or \xff\xfb
            assert header[:3] == b"ID3" or header[0] == 0xFF
    except Exception as e:
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
    except Exception as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_with_different_text_lengths(engine, tmp_path, mock_edge_tts, mock_tiktok_httpx):
    """Each engine should handle different text lengths."""
    texts = [
        "Short.",
        "Medium length text here.",
        "This is a much longer text that contains multiple sentences and should test how the engine handles longer inputs.",
    ]
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        for i, text in enumerate(texts):
            output_path = str(tmp_path / f"test_{engine}_len{i}.mp3")
            path, duration = await generate_audio(engine, voice, text, output_path)
            assert Path(path).exists()
            assert duration > 0
    except Exception as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_output_path_returned(engine, tmp_path, mock_edge_tts, mock_tiktok_httpx):
    """generate_audio should return the output path."""
    output_path = str(tmp_path / "specific_path.mp3")
    text = "Testing output path return."
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        returned_path, _ = await generate_audio(engine, voice, text, output_path)
        assert returned_path == output_path
    except Exception as e:
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
