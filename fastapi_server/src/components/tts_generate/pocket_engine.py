"""
Pocket TTS - 100M params, CPU-only, voice cloning support.
"""

from __future__ import annotations

import tempfile
from dataclasses import dataclass
from pathlib import Path

from scipy.io import wavfile


@dataclass
class VoiceInfo:
    """Information about a voice."""

    name: str
    description: str


VOICES = [
    VoiceInfo("alba", "Default English voice (alba)"),
    VoiceInfo("aoede", "Default English voice (aoede)"),
    VoiceInfo("emma", "Default English voice (emma)"),
    VoiceInfo("fred", "Default English voice (fred)"),
    VoiceInfo("jessie", "Default English voice (jessie)"),
    VoiceInfo("katherine", "Default English voice (katherine)"),
    VoiceInfo("kenny", "Default English voice (kenny)"),
    VoiceInfo("liam", "Default English voice (liam)"),
    VoiceInfo("marcus", "Default English voice (marcus)"),
    VoiceInfo("nicole", "Default English voice (nicole)"),
    VoiceInfo("river", "Default English voice (river)"),
    VoiceInfo("sarah", "Default English voice (sarah)"),
    VoiceInfo("sky", "Default English voice (sky)"),
]

# Global model instance
_pocket_model = None


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Pocket TTS voices."""
    return VOICES


async def _get_pocket_model():
    """Get or initialize the Pocket TTS model (lazy loading)."""
    global _pocket_model

    if _pocket_model is None:
        from pocket_tts import TTSModel

        _pocket_model = TTSModel.load_model()

    return _pocket_model


async def generate_audio_async(
    voice: str,
    text: str,
    output_path: str | None = None,
) -> tuple[str, float]:
    """
    Generate audio using Pocket TTS.

    Args:
        voice: Voice name (e.g., "alba") or audio prompt path/URL
        text: Text to synthesize
        output_path: Optional output path. If None, a temp file is created.

    Returns:
        Tuple of (output_path, duration_seconds)
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    model = await _get_pocket_model()

    # Get voice state - voice can be name, audio path, or HF URL
    voice_state = model.get_state_for_audio_prompt(voice)

    # Generate audio - returns 1D torch tensor
    audio_tensor = model.generate_audio(voice_state, text)

    # Convert torch tensor to numpy
    audio_data = audio_tensor.cpu().numpy()

    # Get sample rate
    sample_rate = model.sample_rate

    # Save as wav first
    wav_path = output_path.replace(".mp3", ".wav")
    wavfile.write(wav_path, sample_rate, audio_data)

    # Convert to mp3
    from pydub import AudioSegment

    audio_segment = AudioSegment.from_wav(wav_path)
    audio_segment.export(output_path, format="mp3")
    Path(wav_path).unlink()

    # Calculate duration
    duration = len(audio_data) / sample_rate

    return output_path, duration
