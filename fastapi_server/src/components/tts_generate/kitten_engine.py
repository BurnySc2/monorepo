"""
KittenTTS - Ultra-lightweight CPU-friendly TTS (15-80M params).
https://github.com/KittenML/KittenTTS
https://kittenml-kittentts.mintlify.app/concepts/voices

Requires espeak-ng installed on system
"""

from __future__ import annotations

import io
import tempfile
import wave

from pydub import AudioSegment

from components.tts_generate._voice_info import VoiceInfo

VOICES = [
    VoiceInfo(name="expr-voice-2-f", short_name="bella", gender="Female", locale="en-us"),
    VoiceInfo(name="expr-voice-2-m", short_name="jasper", gender="Male", locale="en-us"),
    VoiceInfo(name="expr-voice-3-f", short_name="luna", gender="Female", locale="en-us"),
    VoiceInfo(name="expr-voice-3-m", short_name="bruno", gender="Male", locale="en-us"),
    VoiceInfo(name="expr-voice-4-f", short_name="rosie", gender="Female", locale="en-us"),
    VoiceInfo(name="expr-voice-4-m", short_name="hugo", gender="Male", locale="en-us"),
    VoiceInfo(name="expr-voice-5-f", short_name="kiki", gender="Female", locale="en-us"),
    VoiceInfo(name="expr-voice-5-m", short_name="leo", gender="Male", locale="en-us"),
]


async def list_voices_async() -> list[VoiceInfo]:
    """List all available KittenTTS voices."""
    return VOICES


def _get_voice_by_short(short_name: str) -> VoiceInfo | None:
    for v in VOICES:
        if v.short_name == short_name:
            return v
    return None


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

    voice_info = _get_voice_by_short(voice)
    actual_voice = voice_info.name if voice_info else voice

    tts = KittenTTS()
    samples = tts.generate(text, voice=actual_voice, speed=1.0)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(samples.tobytes())
    wav_io.seek(0)

    from pathlib import Path

    audio = AudioSegment.from_wav(wav_io)
    mp3_io = io.BytesIO()
    audio.export(mp3_io, format="mp3")
    mp3_io.seek(0)

    Path(output_path).write_bytes(mp3_io.read())

    from mutagen.mp3 import MP3

    audio = MP3(output_path)
    duration = audio.info.length

    return output_path, duration


async def main() -> None:
    """Run to list all voices and generate a sample MP3."""
    from loguru import logger

    voices = await list_voices_async()
    logger.info(f"Found {len(voices)} voices:")
    for voice in voices:
        display = voice.short_name or voice.name
        logger.info(f"  {display} ({voice.gender}, {voice.locale}) - {voice.name}")

    sample_voice = "Jasper"
    sample_text = "Hello from KittenTTS! This is a test."

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_path, duration = await generate_audio_async(sample_voice, sample_text)
    logger.success(f"Audio saved to: {audio_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
