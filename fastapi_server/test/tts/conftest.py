"""Shared fixtures for TTS tests."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Import from module - ENGINES, CLOUD_ENGINES, LOCAL_ENGINES are defined in __init__.py

# Cloud engines (HTTP-based, can be mocked)
CLOUD_ENGINES = ["edge", "tiktok"]

# Local engines (require model loading)
LOCAL_ENGINES = ["kokoro", "kitten", "pocket", "supertonic"]


@pytest.fixture
def sample_text():
    """Sample text for TTS generation."""
    return "Hello, this is a test of the text to speech system."


@pytest.fixture
def short_text():
    """Short text for quick tests."""
    return "Testing."


@pytest.fixture
def temp_output(tmp_path):
    """Provide a temporary output path for audio files."""
    output_file = tmp_path / "test_output.mp3"
    yield str(output_file)
    # Cleanup handled by tmp_path fixture


@pytest.fixture
def edge_voice():
    """Default voice for Edge TTS."""
    return "en-US-AriaNeural"


@pytest.fixture
def kokoro_voice():
    """Default voice for Kokoro TTS."""
    return "af_bella"


@pytest.fixture
def tiktok_voice():
    """Default voice for TikTok TTS."""
    return "en_us_002"


@pytest.fixture
def supertonic_voice():
    """Default voice for Supertonic TTS."""
    return "F1"


@pytest.fixture
def pocket_voice():
    """Default voice for Pocket TTS."""
    return "alba"


@pytest.fixture
def kitten_voice():
    """Default voice for Kitten TTS."""
    return "default"
