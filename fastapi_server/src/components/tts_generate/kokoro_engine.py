"""
Kokoro TTS - 82M params, CPU-friendly, OpenAI-compatible ONNX model.
https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md
https://github.com/thewh1teagle/kokoro-onnx
"""

from __future__ import annotations

import shutil
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import httpx
import soundfile as sf
from cachetools import TTLCache
from kokoro_onnx import Kokoro
from pydub import audio_segment


@dataclass
class VoiceInfo:
    """Information about a voice."""

    name: str
    short_name: str
    gender: str
    locale: str


_voice_cache: TTLCache = TTLCache(maxsize=1, ttl=300)

_local_dir = Path(__file__).parents[3] / "data" / "kokoro-onnx"
_model_path = _local_dir / "kokoro-v1.0.onnx"
_voices_path = _local_dir / "voices-v1.0.bin"
_MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
_VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"


def _download_file(url: str, target: Path) -> None:
    """Download file to a temp dir, then move to target on completion."""
    if target.exists():
        return
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir) / target.name
        with httpx.Client() as client:
            response = client.get(url, follow_redirects=True)
            response.raise_for_status()
            with tmp_path.open("wb") as f:
                f.write(response.content)
        shutil.move(tmp_path, target)


_local_dir.mkdir(parents=True, exist_ok=True)
_download_file(_MODEL_URL, _model_path)
_download_file(_VOICES_URL, _voices_path)

kokoro = Kokoro(_model_path, _voices_path)


_VOICE_PREFIX_MAP = {
    "af": ("en-us", "Female"),
    "am": ("en-us", "Male"),
    "bf": ("en-gb", "Female"),
    "bm": ("en-gb", "Male"),
    "ef": ("fr-fr", "Female"),
    "em": ("en-gb", "Male"),
    "ff": ("fr-fr", "Female"),
    "hf": ("es-es", "Female"),
    "hm": ("es-es", "Male"),
    "if": ("it-it", "Female"),
    "im": ("it-it", "Male"),
    "jf": ("ja-jp", "Female"),
    "jm": ("ja-jp", "Male"),
    "pf": ("pt-pt", "Female"),
    "pm": ("pt-pt", "Male"),
    "zf": ("zh-cn", "Female"),
    "zm": ("zh-cn", "Male"),
}


def _parse_voice_info(voice_name: str) -> tuple[str, str]:
    """Parse language and gender from voice name prefix."""
    prefix = voice_name.split("_")[0]
    return _VOICE_PREFIX_MAP.get(prefix, ("en-us", "Unknown"))


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Kokoro TTS voices."""
    if "voices" not in _voice_cache:
        raw_voices = kokoro.get_voices()
        _voice_cache["voices"] = [
            VoiceInfo(
                name=v,
                short_name=v,
                gender=_parse_voice_info(v)[1],
                locale=_parse_voice_info(v)[0],
            )
            for v in raw_voices
        ]
    return _voice_cache["voices"]


async def generate_audio_async(
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using Kokoro TTS.

    Args:
        voice: Voice name (e.g., "af_bella")
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """

    samples, sample_rate = kokoro.create(text, voice=voice, speed=1.0, lang="en-us")

    wav_io = BytesIO()
    sf.write(wav_io, samples, sample_rate, format="WAV")
    wav_io.seek(0)

    audio = audio_segment.AudioSegment.from_wav(wav_io)

    mp3_io = BytesIO()
    audio.export(mp3_io, format="mp3")
    mp3_io.seek(0)

    duration = len(samples) / sample_rate

    return mp3_io.read(), duration


async def main() -> None:
    """Run to list all voices and generate a sample MP3."""
    from pathlib import Path

    from loguru import logger

    voices = await list_voices_async()
    logger.info(f"Found {len(voices)} voices:")
    for voice in voices:
        logger.info(f"  {voice.name} ({voice.gender}, {voice.locale})")

    sample_voice = "af_bella"
    sample_text = "Hello from Kokoro TTS! This is a test."
    output_path = Path(__file__).parent / "sample_kokoro.mp3"

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_bytes, duration = await generate_audio_async(sample_voice, sample_text)
    with output_path.open("wb") as f:
        f.write(audio_bytes)
    logger.success(f"Audio saved to: {output_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
