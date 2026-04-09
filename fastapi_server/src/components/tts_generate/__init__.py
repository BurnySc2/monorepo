"""
Unified TTS generation interface.

Provides a unified API for multiple TTS engines:
- edge: Microsoft Edge TTS (cloud, free)
- kokoro: Kokoro TTS (local, CPU-friendly)
- kitten: KittenTTS (local, ultra-lightweight)
- pocket: Pocket TTS (local, voice cloning)
- supertonic: Supertonic TTS (local, fast)
- tiktok: TikTok TTS (cloud, unofficial)
"""

from __future__ import annotations

from typing import Literal

from . import edge_engine, kokoro_engine, pocket_engine, supertonic_engine, tiktok_engine
from ._voice_info import VoiceInfo


# Supported TTS engines
TTSEngine = Literal["edge", "kokoro", "kitten", "pocket", "supertonic", "tiktok"]

# List of all engine names for convenience
ENGINES: list[TTSEngine] = ["edge", "kokoro", "kitten", "pocket", "supertonic", "tiktok"]


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
    elif engine == "supertonic":
        voices = await supertonic_engine.list_voices_async()
    elif engine == "tiktok":
        voices = await tiktok_engine.list_voices_async()
    else:
        raise ValueError(
            f"Unknown TTS engine: {engine}. Supported engines: edge, kokoro, kitten, pocket, supertonic, tiktok"
        )

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


async def generate_audio(
    engine: TTSEngine,
    voice: str,
    text: str,
    output_path: str | None = None,
) -> tuple[str, float]:
    """
    Generate audio using the specified TTS engine.

    Args:
        engine: TTS engine name (edge, kokoro, kitten, pocket, supertonic, tiktok)
        voice: Voice name/code (engine-specific)
        text: Text to synthesize
        output_path: Optional output path. If None, a temp file is created.

    Returns:
        Tuple of (output_path, duration_seconds)

    Raises:
        ValueError: If engine is not supported
    """
    engine = engine.lower()

    if engine == "edge":
        return await edge_engine.generate_audio_async(voice, text, output_path)
    elif engine == "kokoro":
        return await kokoro_engine.generate_audio_async(voice, text, output_path)
    elif engine == "kitten":
        return await kitten_engine.generate_audio_async(voice, text, output_path)
    elif engine == "pocket":
        return await pocket_engine.generate_audio_async(voice, text, output_path)
    elif engine == "supertonic":
        return await supertonic_engine.generate_audio_async(voice, text, output_path)
    elif engine == "tiktok":
        return await tiktok_engine.generate_audio_async(voice, text, output_path)
    else:
        raise ValueError(
            f"Unknown TTS engine: {engine}. Supported engines: edge, kokoro, kitten, pocket, supertonic, tiktok"
        )


# Export all engines for direct access
__all__ = [
    "VoiceInfo",
    "TTSEngine",
    "ENGINES",
    "list_voices",
    "generate_audio",
    "edge_engine",
    "kokoro_engine",
    "kitten_engine",
    "pocket_engine",
    "supertonic_engine",
    "tiktok_engine",
]
