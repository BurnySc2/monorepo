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
from typing import Any

from cachetools import TTLCache
from mutagen.mp3 import MP3

from schemas.tts import ENGINES, TTSEngine, VoiceInfo

from . import edge_engine, kitten_engine, kokoro_engine, tiktok_engine

_all_voices_cache: TTLCache = TTLCache(maxsize=50, ttl=600)
_label_to_voice_info: dict[tuple[str, str], VoiceInfo] = {}

ENGINE_REGISTRY: dict[str, Any] = {
    "edge": edge_engine,
    "kokoro": kokoro_engine,
    "kitten": kitten_engine,
    "tiktok": tiktok_engine,
}


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
    normalized_engine = engine.lower()

    handler = ENGINE_REGISTRY.get(normalized_engine)
    if handler is None:
        raise ValueError(f"Unknown TTS engine: {normalized_engine}. Supported engines: edge, kokoro, kitten, tiktok")

    voices = await handler.list_voices_async()
    return voices


async def list_all_voices() -> list[VoiceInfo]:
    """List all available voices from all TTS engines as VoiceInfo objects."""
    global _label_to_voice_info
    if "voices" not in _all_voices_cache:
        result: list[VoiceInfo] = []
        label_map: dict[tuple[str, str], VoiceInfo] = {}
        for engine in ENGINES:
            voices = await list_voices(engine)
            result.extend(voices)
            for vi in voices:
                label_map[(engine, vi.label.lower())] = vi
        result.sort(key=lambda v: f"{v.locale} {v.engine} {v.label} ({v.gender})")
        _all_voices_cache["voices"] = result
        _label_to_voice_info = label_map
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

    normalized_engine: str = engine.lower()

    handler = ENGINE_REGISTRY.get(normalized_engine)
    if handler is None:
        raise ValueError(f"Unknown TTS engine: {normalized_engine}. Supported engines: edge, kokoro, kitten, tiktok")

    # Populate or update the cache
    _voices = await list_all_voices()
    voice = get_voice_by_label(normalized_engine, voice_label)
    if voice is None:
        raise ValueError(f"Voice '{voice_label}' not found")

    audio_bytes, _ = await handler.generate_audio_async(voice.internal_name, text)

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
    "ENGINE_REGISTRY",
    "list_voices",
    "list_all_voices",
    "generate_audio",
    "get_voice_by_label",
    "edge_engine",
    "kokoro_engine",
    "kitten_engine",
    "tiktok_engine",
]
