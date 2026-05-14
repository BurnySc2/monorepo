"""
Unified TTS generation interface.

Provides a unified API for multiple TTS engines:
- edge: Microsoft Edge TTS (cloud, free)
- kokoro: Kokoro TTS (local, CPU-friendly)
- kitten: KittenTTS (local, ultra-lightweight)
- tiktok: TikTok TTS (cloud, unofficial)
"""

from __future__ import annotations

from io import BytesIO

from cachetools import TTLCache
from mutagen.mp3 import MP3

from schemas.tts import ENGINES, TTSEngine, VoiceInfo

from . import edge_engine, kitten_engine, kokoro_engine, tiktok_engine

_all_voices_cache: TTLCache = TTLCache(maxsize=50, ttl=600)
_label_to_voice_info: dict[tuple[str, str], VoiceInfo] = {}


async def list_voices(engine: TTSEngine) -> list[VoiceInfo]:
    """
    List all available voices for a given TTS engine.

    Args:
        engine: TTS engine name (edge, kokoro, kitten, supertonic, tiktok)

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
    elif engine == "tiktok":
        voices = await tiktok_engine.list_voices_async()
    else:
        raise ValueError(f"Unknown TTS engine: {engine}. Supported engines: edge, kokoro, kitten, tiktok")

    return voices


async def list_all_voices() -> list[VoiceInfo]:
    """List all available voices from all TTS engines as VoiceInfo objects."""
    global _label_to_voice_info
    if "voices" not in _all_voices_cache:
        result: list[VoiceInfo] = []
        for engine in ENGINES:
            voices = await list_voices(engine)
            result.extend(voices)
        result.sort(key=lambda v: f"{v.locale} {v.engine} {v.label} ({v.gender})")
        _all_voices_cache["voices"] = result
        _label_to_voice_info = {}
        for engine in ENGINES:
            engine_voices = await list_voices(engine)
            for vi in engine_voices:
                _label_to_voice_info[(engine, vi.label.lower())] = vi
    return _all_voices_cache["voices"]


async def generate_audio(
    engine: TTSEngine,
    voice_label: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using the specified TTS engine.

    Args:
        engine: TTS engine name (edge, kokoro, kitten, supertonic, tiktok)
        voice: Voice name/code (engine-specific)
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)

    Raises:
        ValueError: If engine is not supported
    """

    engine = engine.lower()

    if engine not in ("edge", "kokoro", "kitten", "tiktok"):
        raise ValueError(f"Unknown TTS engine: {engine}. Supported engines: edge, kokoro, kitten, tiktok")

    # Populate or update the cache
    _voices = await list_all_voices()
    voice = get_voice_by_label(engine, voice_label)
    if voice is None:
        raise ValueError(f"Voice '{voice_label}' not found")

    if engine == "edge":
        audio_bytes, _ = await edge_engine.generate_audio_async(voice.internal_name, text)
    elif engine == "kokoro":
        audio_bytes, _ = await kokoro_engine.generate_audio_async(voice.internal_name, text)
    elif engine == "kitten":
        audio_bytes, _ = await kitten_engine.generate_audio_async(voice.internal_name, text)
    elif engine == "tiktok":
        audio_bytes, _ = await tiktok_engine.generate_audio_async(voice.internal_name, text)
    else:
        raise ValueError(f"Unknown TTS engine: {engine}. Supported engines: edge, kokoro, kitten, tiktok")

    mp3_io = BytesIO(audio_bytes)
    audio = MP3(mp3_io)
    duration = audio.info.length

    return audio_bytes, duration


def get_voice_by_label(engine: str, label: str) -> VoiceInfo | None:
    """Look up a VoiceInfo by its label and optionally by engine."""

    def normalize_from_frontend(v: str) -> str:
        return v.lower().replace("_", " ")

    return _label_to_voice_info.get((engine, normalize_from_frontend(label)))


# Export all engines for direct access
__all__ = [
    "VoiceInfo",
    "TTSEngine",
    "ENGINES",
    "list_voices",
    "list_all_voices",
    "generate_audio",
    "get_voice_by_label",
    "edge_engine",
    "kokoro_engine",
    "kitten_engine",
    "tiktok_engine",
]
