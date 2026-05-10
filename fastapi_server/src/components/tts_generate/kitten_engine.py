"""
KittenTTS - Ultra-lightweight CPU-friendly TTS (15-80M params).
https://github.com/KittenML/KittenTTS
https://kittenml-kittentts.mintlify.app/concepts/voices
https://github.com/second-state/kitten_tts_rs

Requires espeak-ng installed on system
"""

from __future__ import annotations

import asyncio
import io
import tarfile
import tempfile
import urllib.request
import wave
from pathlib import Path

import numpy as np
from pydub import audio_segment

from schemas.tts import VoiceInfo

_local_dir = Path(__file__).parents[3] / "data" / "kitten-tts"
_binary_path = _local_dir / "kitten-tts-x86_64-linux" / "kitten-tts"
_model_dir = _local_dir / "models" / "kitten-tts-mini"
_model_url = "https://github.com/second-state/kitten_tts_rs/releases/latest/download/kitten-tts-models.tar.gz"
_binary_url = "https://github.com/second-state/kitten_tts_rs/releases/latest/download/kitten-tts-x86_64-linux.tar.gz"


def _download_file(url: str, dest: Path) -> None:
    urllib.request.urlretrieve(url, dest)


def _get_binary_path() -> Path:
    if _binary_path.exists():
        return _binary_path
    _local_dir.mkdir(parents=True, exist_ok=True)
    tmp_tar = _local_dir / "kitten-tts.tar.gz"
    _download_file(_binary_url, tmp_tar)
    with tarfile.open(tmp_tar) as tf:
        tf.extractall(_local_dir)
    tmp_tar.unlink()
    return _binary_path


def _ensure_models() -> Path:
    if _model_dir.exists() and (_model_dir / "config.json").exists():
        return _model_dir
    _local_dir.mkdir(parents=True, exist_ok=True)
    tmp_tar = _local_dir / "kitten-tts-models.tar.gz"
    _download_file(_model_url, tmp_tar)
    with tarfile.open(tmp_tar) as tf:
        tf.extractall(_local_dir)
    tmp_tar.unlink()
    return _model_dir


_binary_exe: Path | None = None


async def _get_binary() -> Path:
    global _binary_exe
    if _binary_exe is None:
        _binary_exe = _get_binary_path()
        _ensure_models()
    return _binary_exe


VOICES = [
    VoiceInfo(engine="kitten", internal_name="Bella", label="Bella", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="Jasper", label="Jasper", gender="Male", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="Luna", label="Luna", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="Bruno", label="Bruno", gender="Male", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="Rosie", label="Rosie", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="Hugo", label="Hugo", gender="Male", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="Kiki", label="Kiki", gender="Female", locale="en-us"),
    VoiceInfo(engine="kitten", internal_name="Leo", label="Leo", gender="Male", locale="en-us"),
]


async def list_voices_async() -> list[VoiceInfo]:
    """List all available KittenTTS voices."""
    return VOICES


async def generate_audio_async(
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using KittenTTS binary.

    Args:
        voice: Voice name (e.g., "Jasper")
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """
    voices = await list_voices_async()
    if voice not in [v.internal_name for v in voices]:
        raise ValueError(f"Voice '{voice}' not found. Available: {[v.internal_name for v in voices]}")

    binary = await _get_binary()

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / "output.wav"

        proc = await asyncio.create_subprocess_exec(
            str(binary),
            str(_model_dir),
            text,
            "--voice",
            voice,
            "--output",
            str(tmp_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"kitten-tts failed: {stderr.decode()}")

        with wave.open(str(tmp_path), "rb") as wf:
            duration = wf.getnframes() / wf.getframerate()
            frames = wf.readframes(wf.getnframes())

    samples_int16 = np.frombuffer(frames, dtype=np.int16)

    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(24000)
        wav_file.writeframes(samples_int16.tobytes())
    wav_io.seek(0)

    audio = audio_segment.AudioSegment.from_wav(wav_io)
    mp3_io = io.BytesIO()
    audio_segment.AudioSegment.export(audio, mp3_io, format="mp3")
    mp3_io.seek(0)

    return mp3_io.read(), duration


async def main() -> None:
    """Run to list all voices and generate a sample MP3."""
    from loguru import logger

    voices = await list_voices_async()
    logger.info(f"Found {len(voices)} voices:")
    for voice in voices:
        logger.info(f"  {voice.label or voice.internal_name} ({voice.gender}, {voice.locale}) - {voice.internal_name}")

    sample_voice = "Jasper"
    sample_text = "Welcome to the Kitten TTS testing suite. This is a comprehensive boundary condition test designed to verify that the text-to-speech engine can handle longer inputs without truncation or errors. We include various punctuation marks, multiple sentences, and diverse linguistic structures to ensure robust handling of edge cases. The quick brown fox jumps over the lazy dog while keeping your sample text interesting and varied. Numbers like 12345 and symbols like @#$% are also included. This tests all aspects of text generation including commas, periods, question marks, exclamation points, colons, semicolons, hyphens, and parentheses. Even the occasional dash or apostrophe is included to make sure the system handles them all correctly."  # noqa: E501
    output_path = Path(__file__).parent / "sample_kitten.mp3"

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_bytes, duration = await generate_audio_async(sample_voice, sample_text)
    with output_path.open("wb") as f:
        f.write(audio_bytes)
    logger.success(f"Audio saved to: {output_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    asyncio.run(main())
