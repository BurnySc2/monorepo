"""
Supertonic TTS - 66M params, CPU-optimized, 167x real-time, 10 languages.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path


@dataclass
class VoiceInfo:
    """Information about a voice."""

    name: str
    gender: str
    description: str


VOICES = [
    VoiceInfo("F1", "Female", "Female voice style 1"),
    VoiceInfo("F2", "Female", "Female voice style 2"),
    VoiceInfo("F3", "Female", "Female voice style 3"),
    VoiceInfo("F4", "Female", "Female voice style 4"),
    VoiceInfo("F5", "Female", "Female voice style 5"),
    VoiceInfo("M1", "Male", "Male voice style 1"),
    VoiceInfo("M2", "Male", "Male voice style 2"),
    VoiceInfo("M3", "Male", "Male voice style 3"),
    VoiceInfo("M4", "Male", "Male voice style 4"),
    VoiceInfo("M5", "Male", "Male voice style 5"),
]

# Global model instance
_supertonic_model = None


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Supertonic TTS voices."""
    return VOICES


async def _get_supertonic_model():
    """Get or initialize the Supertonic model (lazy loading)."""
    global _supertonic_model

    if _supertonic_model is None:
        from supertonic import TTS

        _supertonic_model = TTS()

    return _supertonic_model


async def generate_audio_async(
    voice: str,
    text: str,
    output_path: str | None = None,
) -> tuple[str, float]:
    """
    Generate audio using Supertonic TTS.

    Args:
        voice: Voice style name (e.g., "F1", "M3")
        text: Text to synthesize
        output_path: Optional output path. If None, a temp file is created.

    Returns:
        Tuple of (output_path, duration_seconds)
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    tts = await _get_supertonic_model()

    # Get voice style
    voice_style = tts.get_voice_style(voice)

    # Generate audio - synthesize returns (audio_data, sample_rate)
    audio_data, sample_rate = tts.synthesize(text, voice_style=voice_style)

    # Handle different audio formats - Supertonic may return (1, N) shape

    if len(audio_data.shape) > 1:
        audio_data = audio_data.squeeze()

    # Save audio as WAV first
    wav_path = output_path.replace(".mp3", ".wav")
    tts.save_audio(audio_data, wav_path)

    # Convert to MP3 using pydub
    from pydub import AudioSegment

    audio_segment = AudioSegment.from_wav(wav_path)
    audio_segment.export(output_path, format="mp3")
    Path(wav_path).unlink()

    # Calculate duration
    duration = len(audio_data) / sample_rate

    return output_path, duration
