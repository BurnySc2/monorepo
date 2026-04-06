"""
Kokoro TTS - 82M params, CPU-friendly, OpenAI-compatible ONNX model.
Voice names: af_bella, af_nicole, af_sarah, af_sky, bf_alice, bf_emma, bf_isabella, bf_lily
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass

import numpy as np
import soundfile as sf
from huggingface_hub import snapshot_download


@dataclass
class VoiceInfo:
    """Information about a voice."""
    name: str
    gender: str
    description: str


VOICES = [
    VoiceInfo("af_bella", "Female", "American English - Bella"),
    VoiceInfo("af_nicole", "Female", "American English - Nicole"),
    VoiceInfo("af_sarah", "Female", "American English - Sarah"),
    VoiceInfo("af_sky", "Female", "American English - Sky"),
    VoiceInfo("bf_alice", "Female", "British English - Alice"),
    VoiceInfo("bf_emma", "Female", "British English - Emma"),
    VoiceInfo("bf_isabella", "Female", "British English - Isabella"),
    VoiceInfo("bf_lily", "Female", "British English - Lily"),
    VoiceInfo("pf_london", "Female", "British English - London"),
    VoiceInfo("pm_johnny", "Male", "American English - Johnny"),
    VoiceInfo("pm_george", "Male", "American English - George"),
    VoiceInfo("pm_lucio", "Male", "American English - Lucio"),
    VoiceInfo("pm_ryan", "Male", "American English - Ryan"),
    VoiceInfo("pm_daniel", "Male", "British English - Daniel"),
    VoiceInfo("pm_liam", "Male", "British English - Liam"),
]

# Global model instance
_kokoro_model = None
_model_dir = None


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Kokoro TTS voices."""
    return VOICES


async def _get_kokoro_model():
    """Get or initialize the Kokoro model (lazy loading)."""
    global _kokoro_model, _model_dir

    if _kokoro_model is None:
        from kokoro_onnx import Kokoro, EspeakConfig

        # Download model if not cached
        _model_dir = snapshot_download(repo_id="adrianlyjak/kokoro-onnx")
        model_path = os.path.join(_model_dir, "kokoro-v1.0.onnx")
        voices_path = os.path.join(_model_dir, "voices.bin")

        # Configure espeak-ng
        espeak_data = "/usr/lib/x86_64-linux-gnu/espeak-ng-data"
        espeak_config = EspeakConfig(data_path=espeak_data)

        _kokoro_model = Kokoro(model_path, voices_path, espeak_config=espeak_config)

    return _kokoro_model


async def generate_audio_async(
    voice: str,
    text: str,
    output_path: str | None = None,
) -> tuple[str, float]:
    """
    Generate audio using Kokoro TTS.

    Args:
        voice: Voice name (e.g., "af_bella")
        text: Text to synthesize
        output_path: Optional output path. If None, a temp file is created.

    Returns:
        Tuple of (output_path, duration_seconds)
    """
    if output_path is None:
        output_path = tempfile.mktemp(suffix=".mp3")

    kokoro = await _get_kokoro_model()

    # Generate audio
    audio, sample_rate = kokoro.create(text, voice=voice)

    # Convert to float32 if needed
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # Normalize to [-1, 1]
    audio = audio / max(np.abs(audio).max(), 1e-6)

    # Save as WAV first
    wav_path = output_path.replace(".mp3", ".wav")
    sf.write(wav_path, audio, sample_rate)

    # Convert to MP3 using pydub
    from pydub import AudioSegment

    audio_segment = AudioSegment.from_wav(wav_path)
    audio_segment.export(output_path, format="mp3")
    os.unlink(wav_path)

    # Calculate duration
    duration = len(audio) / sample_rate

    return output_path, duration
