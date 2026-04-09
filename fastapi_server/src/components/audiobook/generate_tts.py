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
    voice: str,
    rate: int = 0,
    volume: int = 0,
    pitch: int = 0,
) -> io.BytesIO:
    import edge_tts

    from components.tts_generate import generate_audio

    rate_str = f"+{rate}%" if rate >= 0 else f"-{rate}%"
    volume_str = f"+{volume}%" if volume >= 0 else f"-{volume}%"
    pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"-{pitch}Hz"

    if "|" in voice:
        engine, voice_name = parse_voice_value(voice)
        audio_bytes, _ = await generate_audio(engine, voice_name, text)
        return io.BytesIO(audio_bytes)

    result = io.BytesIO()
    communicate = edge_tts.Communicate(text.strip(), voice, rate=rate_str, volume=volume_str, pitch=pitch_str)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            result.write(chunk["data"])
    result.seek(0)
    return result


async def main():
    voices = await get_supported_voices()  # noqa: F841
    text = "Hello World! This is one sentence. What is the second sentence?"
    text = """
Title: The Enduring Legacy of\nStarCraft II: A Saga of Strategy, Esports, and Innovation

Introduction:

Since its release in 2010, StarCraft II\nhas etched its place in gaming history as one of the most iconic real-time strategy (RTS) games of all time. Developed by Blizzard\nEntertainment, StarCraft II is the\nsequel to the original StarCraft, a game\nthat revolutionized the RTS genre in the late 1990s. In this essay, we will delve into the multifaceted world of StarCraft II, exploring its gameplay mechanics, its impact on esports, its enduring legacy, and its contributions to the gaming industry.
"""  # noqa: E501
    voice = "en-GB-SoniaNeural"
    result = await generate_text_to_speech(text, voice)  # noqa: F841
    # with Path("asd.mp3").open("wb") as f:
    #     f.write(result.getvalue())


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
