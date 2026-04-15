"""
KittenTTS - Ultra-lightweight CPU-friendly TTS (15-80M params).
https://github.com/KittenML/KittenTTS
https://kittenml-kittentts.mintlify.app/concepts/voices

TODO Use binary instead https://github.com/second-state/kitten_tts_rs

Requires espeak-ng installed on system
"""

from __future__ import annotations

import io
import json
import wave
from pathlib import Path

import numpy as np
from kittentts.onnx_model import KittenTTS_1_Onnx
from pydub import AudioSegment

from components.tts_generate._download import download_file
from schemas.tts import VoiceInfo

_local_dir = Path(__file__).parents[3] / "data" / "kitten-tts-mini-0.8"
_CONFIG_URL = "https://huggingface.co/KittenML/kitten-tts-mini-0.8/resolve/main/config.json"
_MODEL_URL = "https://huggingface.co/KittenML/kitten-tts-mini-0.8/resolve/main/kitten_tts_mini_v0_8.onnx"
_VOICES_URL = "https://huggingface.co/KittenML/kitten-tts-mini-0.8/resolve/main/voices.npz"

_local_dir.mkdir(parents=True, exist_ok=True)


def _get_model_paths():
    config_path = _local_dir / "config.json"
    download_file(_CONFIG_URL, config_path)
    with config_path.open() as f:
        config = json.load(f)
    model_path = _local_dir / "kitten_tts_mini_v0_8.onnx"
    voices_path = _local_dir / "voices.npz"
    download_file(_MODEL_URL, model_path)
    download_file(_VOICES_URL, voices_path)
    return model_path, voices_path, config


_model_path, _voices_path, _config = _get_model_paths()

_tts_model = KittenTTS_1_Onnx(
    model_path=str(_model_path),
    voices_path=str(_voices_path),
    speed_priors=_config.get("speed_priors", {}),
    voice_aliases=_config.get("voice_aliases", {}),
)

VOICES = [
    VoiceInfo(engine="kitten", internal_name="expr-voice-2-f", label="Bella", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="expr-voice-2-m", label="Jasper", gender="Male", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="expr-voice-3-f", label="Luna", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="expr-voice-3-m", label="Bruno", gender="Male", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="expr-voice-4-f", label="Rosie", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="expr-voice-4-m", label="Hugo", gender="Male", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="expr-voice-5-f", label="Kiki", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="expr-voice-5-m", label="Leo", gender="Male", locale="en-us"),
]


async def list_voices_async() -> list[VoiceInfo]:
    """List all available KittenTTS voices."""
    return VOICES


async def generate_audio_async(
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using KittenTTS.

    Args:
        voice: Voice name (e.g., "jasper")
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """

    samples = _tts_model.generate(text, voice=voice, speed=1.0)

    samples_int16 = (samples * 32767).astype(np.int16)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(samples_int16.tobytes())
    wav_io.seek(0)

    audio = AudioSegment.from_wav(wav_io)
    mp3_io = io.BytesIO()
    audio.export(mp3_io, format="mp3")
    mp3_io.seek(0)

    duration = len(samples) / 24000

    return mp3_io.read(), duration


async def main() -> None:
    """Run to list all voices and generate a sample MP3."""
    from loguru import logger

    voices = await list_voices_async()
    logger.info(f"Found {len(voices)} voices:")
    for voice in voices:
        logger.info(f"  {voice.label or voice.internal_name} ({voice.gender}, {voice.locale}) - {voice.internal_name}")

    sample_voice = "jasper"
    sample_text = "Hello from KittenTTS! This is a test."
    output_path = Path(__file__).parent / "sample_kitten.mp3"

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_bytes, duration = await generate_audio_async(sample_voice, sample_text)
    with output_path.open("wb") as f:
        f.write(audio_bytes)
    logger.success(f"Audio saved to: {output_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
