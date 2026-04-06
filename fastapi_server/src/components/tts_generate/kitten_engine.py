"""
KittenTTS - Ultra-lightweight CPU-friendly TTS (15-80M params).
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass


@dataclass
class VoiceInfo:
    """Information about a voice."""
    name: str
    language: str
    description: str


VOICES = [
    VoiceInfo("default", "en", "Default English voice"),
]


async def list_voices_async() -> list[VoiceInfo]:
    """List all available KittenTTS voices."""
    return VOICES


async def generate_audio_async(
    voice: str,
    text: str,
    output_path: str | None = None,
) -> tuple[str, float]:
    """
    Generate audio using KittenTTS.

    Args:
        voice: Voice name (currently only "default" is supported)
        text: Text to synthesize
        output_path: Optional output path. If None, a temp file is created.

    Returns:
        Tuple of (output_path, duration_seconds)
    """
    from kittentts import KittenTTS

    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    tts = KittenTTS()
    tts.generate_to_file(text, output_path)

    # Get duration using mutagen
    from mutagen.mp3 import MP3

    audio = MP3(output_path)
    duration = audio.info.length

    return output_path, duration
