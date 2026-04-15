"""
Edge TTS - Microsoft free cloud TTS, 74+ languages, 322 voices.
https://github.com/rany2/edge-tts
"""

from __future__ import annotations

from io import BytesIO
from pathlib import Path

import edge_tts
from cachetools import TTLCache
from loguru import logger

from schemas.tts import VoiceInfo

_voice_cache: TTLCache = TTLCache(maxsize=1, ttl=300)


async def list_voices_async() -> list[VoiceInfo]:
    """List all available Edge TTS voices."""
    if "voices" not in _voice_cache:
        raw_voices = await edge_tts.list_voices()
        _voice_cache["voices"] = [
            VoiceInfo(
                engine="edge",
                internal_name=v["Name"],
                label=v["ShortName"].rsplit("-", 1)[-1].capitalize(),
                gender=v["Gender"],
                locale=v["Locale"].lower(),
            )
            for v in raw_voices
        ]
        logger.info(_voice_cache["voices"][0])
    return _voice_cache["voices"]


async def generate_audio_async(
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using Edge TTS.

    Args:
        voice: Voice name (e.g., "en-US-AriaNeural")
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """
    communicate = edge_tts.Communicate(text, voice)
    audio_io = BytesIO()
    async for chunk in communicate.stream():
        if "data" in chunk:
            audio_io.write(chunk["data"])
    audio_io.seek(0)

    duration = max(0.1, len(text) / 10.0)

    return audio_io.read(), duration


async def main() -> None:
    """Run to list all voices and generate a sample MP3."""
    from loguru import logger

    voices = await list_voices_async()
    logger.info(f"Found {len(voices)} voices:")
    for voice in voices:
        logger.info(f"  {voice.internal_name} ({voice.gender}, {voice.locale})")

    sample_voice = "en-US-AriaNeural"
    sample_text = "Hello from Edge TTS! This is a test."
    output_path = Path(__file__).parent / "sample_edge.mp3"

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_bytes, duration = await generate_audio_async(sample_voice, sample_text)
    with output_path.open("wb") as f:
        f.write(audio_bytes)
    logger.success(f"Audio saved to: {output_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
