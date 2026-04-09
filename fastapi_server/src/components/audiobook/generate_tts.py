from __future__ import annotations

import io

from cachetools import TTLCache

from components.tts_generate import VoiceOption, list_all_voices

ttl_cache: TTLCache[str, list[VoiceOption]] = TTLCache(1024, 3600)  # 3600 seconds


async def get_supported_voices() -> list[VoiceOption]:
    """
    Get all voices from all TTS engines with caching.
    """
    global ttl_cache
    # pyrefly: ignore
    result_from_cache = ttl_cache.get("voices")
    if result_from_cache is not None:
        return result_from_cache

    result = await list_all_voices()
    # pyrefly: ignore
    ttl_cache["voices"] = result
    return result


def parse_voice_value(value: str) -> tuple[str, str]:
    """
    Parse voice value into (engine, voice_name).

    Value format: "locale|engine|voice_name|gender"
    Example: "en-us|kokoro|bella|female" -> ("kokoro", "bella")
    """
    parts = value.split("|")
    if len(parts) != 4:
        raise ValueError(f"Invalid voice value format: {value}")
    engine = parts[1]
    voice_name = parts[2]
    return engine, voice_name


async def generate_text_to_speech(
    text: str,
    engine: str,
    voice: str,
) -> io.BytesIO:
    from components.tts_generate import generate_audio

    audio_bytes, _ = await generate_audio(engine, voice, text)
    return io.BytesIO(audio_bytes)


async def main():
    voices = await get_supported_voices()  # noqa: F841
    text = "Hello World! This is one sentence. What is the second sentence?"
    voice = voices[0]
    result = await generate_text_to_speech(text, voice.engine, voice.voice)  # noqa: F841


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
