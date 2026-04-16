"""Parametrized tests for individual TTS engines."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from components.tts_generate import ENGINES, generate_audio, list_voices

# Default voices for each engine
DEFAULT_VOICES = {
    "edge": "arianeural",
    "kokoro": "alloy",
    "kitten": "bella",
    "tiktok": "ghost_face",
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
        Path(output_path).write_bytes(
            b"ID3"  # ID3 tag
            b"\x04\x00\x00\x00\x00\x00\x00" + mp3_data * 10  # ID3 header  # Some MP3 frames
        )

    async def get_audio(self, audio_obj):
        # Edge TTS doesn't have Audio class, it sets duration directly
        if hasattr(audio_obj, "duration"):
            audio_obj.duration = 1.5


@pytest.fixture
def mock_edge_tts():
    """Mock edge_tts module for testing."""
    from io import BytesIO

    import numpy as np
    from pydub import AudioSegment

    from components.tts_generate import edge_engine

    def generate_sine_mp3(voice, text):
        sample_rate = 22050
        duration = max(0.1, len(text) / 10.0)
        freq = 440
        t = np.linspace(0, duration, int(sample_rate * duration))
        samples = (np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
        audio = AudioSegment(
            samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1,
        )
        mp3_io = BytesIO()
        audio.export(mp3_io, format="mp3")
        return mp3_io.read(), duration

    async def mock_generate(voice, text):
        return generate_sine_mp3(voice, text)

    with patch.object(edge_engine, "generate_audio_async", side_effect=mock_generate):
        yield


@pytest.fixture
def mock_tiktok_httpx():
    """Mock httpx for TikTok TTS testing."""
    from io import BytesIO

    import numpy as np
    from pydub import AudioSegment

    from components.tts_generate import tiktok_engine

    def generate_sine_mp3(voice, text):
        sample_rate = 22050
        duration = max(0.1, len(text) / 10.0)
        freq = 440
        t = np.linspace(0, duration, int(sample_rate * duration))
        samples = (np.sin(2 * np.pi * freq * t) * 32767).astype(np.int16)
        audio = AudioSegment(
            samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,
            channels=1,
        )
        mp3_io = BytesIO()
        audio.export(mp3_io, format="mp3")
        return mp3_io.read(), duration

    async def mock_generate(voice, text):
        return generate_sine_mp3(voice, text)

    with patch.object(tiktok_engine, "generate_audio_async", side_effect=mock_generate):
        yield


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_list_voices_returns_non_empty_list(engine):
    """Each engine should return a non-empty list of voices."""
    voices = await list_voices(engine)
    assert isinstance(voices, list)
    assert len(voices) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_voices_have_label_attribute(engine):
    """Each voice should have a non-empty label."""
    voices = await list_voices(engine)
    for voice in voices:
        assert hasattr(voice, "label")
        assert isinstance(voice.label, str)
        assert len(voice.label) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_first_voice_is_valid(engine):
    """The first voice should be valid and usable."""
    voices = await list_voices(engine)
    first_voice = voices[0]
    assert first_voice.label


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_list_voices_idempotent(engine):
    """Calling list_voices multiple times should return consistent results."""
    voices1 = await list_voices(engine)
    voices2 = await list_voices(engine)
    assert len(voices1) == len(voices2)
    names1 = [v.label for v in voices1]
    names2 = [v.label for v in voices2]
    assert names1 == names2


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_with_default_voice(engine, mock_edge_tts, mock_tiktok_httpx):
    """Each engine should generate audio with its default voice."""
    text = "Hello, this is a test."

    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        audio_bytes, duration = await generate_audio(engine, voice, text)
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

        # Check audio has content
        assert len(audio_bytes) > 0

        # Verify it's a valid audio file by checking header
        header = audio_bytes[:4]
        # MP3 files start with ID3 or \xff\xfb
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
async def test_generate_audio_with_different_text_lengths(engine, tmp_path, mock_edge_tts, mock_tiktok_httpx):
    """Each engine should handle different text lengths."""
    texts = [
        "Short.",
        "Medium length text here.",
        "This is a much longer text that contains multiple sentences "
        "and should test how the engine handles longer inputs.",
    ]
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        for i, text in enumerate(texts):
            audio_bytes, duration = await generate_audio(engine, voice, text)
            assert len(audio_bytes) > 0
            assert duration > 0
    except OSError as e:
        pytest.skip(f"Engine {engine} not available: {e}")


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ENGINES)
async def test_generate_audio_output_path_returned(engine, mock_edge_tts, mock_tiktok_httpx):
    """generate_audio should return audio bytes."""
    text = "Testing output path return."
    voice = DEFAULT_VOICES.get(engine, "default")

    try:
        audio_bytes, _ = await generate_audio(engine, voice, text)
        assert len(audio_bytes) > 0
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


@pytest.mark.asyncio
@pytest.mark.parametrize("engine", ["kokoro", "kitten"])
async def test_invalid_voice_raises_valueerror(engine):
    """Invalid voice should raise ValueError."""
    from components.tts_generate import kitten_engine, kokoro_engine

    invalid_voice = "nonexistent_voice_xyz"
    text = "Hello test."

    if engine == "kitten":
        with pytest.raises(ValueError, match="not found"):
            await kitten_engine.generate_audio_async(invalid_voice, text)
    elif engine == "kokoro":
        with pytest.raises(ValueError, match="not found"):
            await kokoro_engine.generate_audio_async(invalid_voice, text)
