"""
Pocket TTS - 100M params, CPU-only, voice cloning support.
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import soundfile as sf
from pydub import AudioSegment

from components.tts_generate._voice_info import VoiceInfo
from pocket_tts import TTSModel


_local_dir = Path(__file__).parents[3] / "data" / "pocket-tts"
_local_dir.mkdir(parents=True, exist_ok=True)

_tts_model = TTSModel.load_model()


VOICES = [
    VoiceInfo(name="alba", short_name="alba", gender="Female", locale="en-us"),
    VoiceInfo(name="aoede", short_name="aoede", gender="Female", locale="en-us"),
    VoiceInfo(name="emma", short_name="emma", gender="Female", locale="en-us"),
    VoiceInfo(name="fred", short_name="fred", gender="Male", locale="en-us"),
    VoiceInfo(name="jessie", short_name="jessie", gender="Female", locale="en-us"),
    VoiceInfo(name="katherine", short_name="katherine", gender="Female", locale="en-us"),
    VoiceInfo(name="kenny", short_name="kenny", gender="Male", locale="en-us"),
    VoiceInfo(name="liam", short_name="liam", gender="Male", locale="en-us"),
    VoiceInfo(name="marcus", short_name="marcus", gender="Male", locale="en-us"),
    VoiceInfo(name="nicole", short_name="nicole", gender="Female", locale="en-us"),
    VoiceInfo(name="river", short_name="river", gender="Male", locale="en-us"),
    VoiceInfo(name="sarah", short_name="sarah", gender="Female", locale="en-us"),
    VoiceInfo(name="sky", short_name="sky", gender="Female", locale="en-us"),
]


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Pocket TTS voices."""
    return VOICES


def _get_voice_by_short(short_name: str) -> VoiceInfo | None:
    for v in VOICES:
        if v.short_name == short_name:
            return v
    return None


async def generate_audio_async(
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using Pocket TTS.

    Args:
        voice: Voice name (e.g., "alba")
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """
    voice_info = _get_voice_by_short(voice)
    actual_voice = voice_info.name if voice_info else voice

    voice_state = _tts_model.get_state_for_audio_prompt(actual_voice)
    audio_tensor = _tts_model.generate_audio(voice_state, text)

    audio_data = audio_tensor.cpu().numpy()
    sample_rate = _tts_model.sample_rate

    wav_io = BytesIO()
    sf.write(wav_io, audio_data, sample_rate, format="WAV")
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
        logger.info(f"  {voice.name} ({voice.gender}, {voice.locale})")

    sample_voice = "alba"
    sample_text = "Hello from Pocket TTS! This is a test."
    output_path = Path(__file__).parent / "sample_pocket.mp3"

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_bytes, duration = await generate_audio_async(sample_voice, sample_text)
    with output_path.open("wb") as f:
        f.write(audio_bytes)
    logger.success(f"Audio saved to: {output_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
