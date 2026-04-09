"""
Pocket TTS - 100M params, CPU-only, voice cloning support.
"""

from __future__ import annotations

from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

from cachetools import TTLCache
from pydub import AudioSegment


@dataclass
class VoiceInfo:
    """Information about a voice."""

    name: str
    description: str


_voice_cache: TTLCache = TTLCache(maxsize=1, ttl=300)

# Global model instance
_pocket_model = None


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Pocket TTS voices."""
    if "voices" not in _voice_cache:
        _voice_cache["voices"] = [
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
    return _voice_cache["voices"]


async def _get_pocket_model():
    """Get or initialize the Pocket TTS model (lazy loading)."""
    global _pocket_model

    if _pocket_model is None:
        _pocket_model = TTSModel.load_model()

    return _pocket_model


async def generate_audio_async(
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using Pocket TTS.

    Args:
        voice: Voice name (e.g., "alba") or audio prompt path/URL
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """

    model = await _get_pocket_model()

    voice_state = model.get_state_for_audio_prompt(voice)
    audio_tensor = model.generate_audio(voice_state, text)

    audio_data = audio_tensor.cpu().numpy()
    sample_rate = model.sample_rate

    wav_io = BytesIO()
    wavfile.write(wav_io, sample_rate, audio_data)
    wav_io.seek(0)

    audio_segment = AudioSegment.from_wav(wav_io)
    mp3_io = BytesIO()
    audio_segment.export(mp3_io, format="mp3")
    mp3_io.seek(0)

    duration = len(audio_data) / sample_rate

    return mp3_io.read(), duration


async def main() -> None:
    """Run to list all voices and generate a sample MP3."""

    from loguru import logger

    voices = await list_voices_async()
    logger.info(f"Found {len(voices)} voices:")
    for voice in voices:
        logger.info(f"  {voice.name} - {voice.description}")

    sample_voice = "alba"
    sample_text = "Hello from Pocket TTS! This is a test."
    output_path = Path("sample_pocket.mp3")

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_bytes, duration = await generate_audio_async(sample_voice, sample_text)
    with output_path.open("wb") as f:
        f.write(audio_bytes)
    logger.success(f"Audio saved to: {output_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
