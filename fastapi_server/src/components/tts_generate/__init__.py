"""
Unified TTS generation interface.

Provides a unified API for multiple TTS engines:
- edge: Microsoft Edge TTS (cloud, free)
- kokoro: Kokoro TTS (local, CPU-friendly)
- kitten: KittenTTS (local, ultra-lightweight)
- pocket: Pocket TTS (local, voice cloning)
- tiktok: TikTok TTS (cloud, unofficial)
"""

from __future__ import annotations

from typing import Literal

from . import edge_engine, kitten_engine, kokoro_engine, pocket_engine, tiktok_engine
from ._types import VoiceOption
from ._voice_info import VoiceInfo

# Supported TTS engines
TTSEngine = Literal["edge", "kokoro", "kitten", "pocket", "tiktok"]

# List of all engine names for convenience
ENGINES: list[TTSEngine] = ["edge", "kokoro", "kitten", "pocket", "tiktok"]


async def list_voices(engine: TTSEngine) -> list[VoiceInfo]:
    """
    List all available voices for a given TTS engine.

    Args:
        engine: TTS engine name (edge, kokoro, kitten, pocket, supertonic, tiktok)

    Returns:
        List of VoiceInfo objects

    Raises:
        ValueError: If engine is not supported
    """
    engine = engine.lower()

    if engine == "edge":
        voices = await edge_engine.list_voices_async()
    elif engine == "kokoro":
        voices = await kokoro_engine.list_voices_async()
    elif engine == "kitten":
        voices = await kitten_engine.list_voices_async()
    elif engine == "pocket":
        voices = await pocket_engine.list_voices_async()
    elif engine == "tiktok":
        voices = await tiktok_engine.list_voices_async()
    else:
        raise ValueError(f"Unknown TTS engine: {engine}. Supported engines: edge, kokoro, kitten, pocket, tiktok")

    # Normalize to VoiceInfo
    result = []
    for v in voices:
        if hasattr(v, "name"):
            result.append(
                VoiceInfo(
                    name=v.name,
                    short_name=getattr(v, "short_name", None),
                    gender=getattr(v, "gender", None),
                    locale=getattr(v, "locale", None),
                    language=getattr(v, "language", None),
                    description=getattr(v, "description", None),
                )
            )
        else:
            result.append(VoiceInfo(name=str(v)))

    return result


async def list_all_voices() -> list[VoiceOption]:
    """List all available voices from all TTS engines as VoiceOption objects."""
    result: list[VoiceOption] = []
    for engine in ENGINES:
        voices = await list_voices(engine)
        for voice in voices:
            result.append(VoiceOption.from_voice_info(voice, engine))
    result.sort(key=lambda v: v.label)
    return result


async def generate_audio(
    engine: TTSEngine,
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using the specified TTS engine.

    Args:
        engine: TTS engine name (edge, kokoro, kitten, pocket, supertonic, tiktok)
        voice: Voice name/code (engine-specific)
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)

    Raises:
        ValueError: If engine is not supported
    """
    from io import BytesIO

    from mutagen.mp3 import MP3

    engine = engine.lower()

    if engine == "edge":
        audio_bytes, _ = await edge_engine.generate_audio_async(voice, text)
    elif engine == "kokoro":
        audio_bytes, _ = await kokoro_engine.generate_audio_async(voice, text)
    elif engine == "kitten":
        audio_bytes, _ = await kitten_engine.generate_audio_async(voice, text)
    elif engine == "pocket":
        audio_bytes, _ = await pocket_engine.generate_audio_async(voice, text)
    elif engine == "tiktok":
        audio_bytes, _ = await tiktok_engine.generate_audio_async(voice, text)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}. Supported engines: edge, kokoro, kitten, pocket, tiktok")

    mp3_io = BytesIO(audio_bytes)
    audio = MP3(mp3_io)
    duration = audio.info.length

    return audio_bytes, duration


# Export all engines for direct access
__all__ = [
    "VoiceInfo",
    "VoiceOption",
    "TTSEngine",
    "ENGINES",
    "list_voices",
    "list_all_voices",
    "generate_audio",
    "edge_engine",
    "kokoro_engine",
    "kitten_engine",
    "pocket_engine",
    "tiktok_engine",
]
