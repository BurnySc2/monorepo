import asyncio
import io

import edge_tts

from src.routes.caches import global_cache


async def get_supported_voices() -> list[str]:
    # Cache result for at least 1h
    global global_cache
    # pyre-fixme[9]
    result_from_cache: list[str] | None = await global_cache.get("voices")
    if result_from_cache is not None:
        return result_from_cache

    voices = await edge_tts.list_voices()
    result = [voice["ShortName"] for voice in sorted(voices, key=lambda voice: voice["ShortName"])]
    # pyre-fixme[6]
    await global_cache.set("voices", result, expires_in=3600)
    return result


async def generate_text_to_speech(
    text: str,
    voice: str,
    rate: int = 0,
    volume: int = 0,
    pitch: int = 0,
) -> io.BytesIO:
    rate_str = f"+{rate}%" if rate >= 0 else f"-{rate}%"
    volume_str = f"+{volume}%" if volume >= 0 else f"-{volume}%"
    pitch_str = f"+{pitch}Hz" if pitch >= 0 else f"-{pitch}Hz"

    result = io.BytesIO()
    meta_info = []
    communicate = edge_tts.Communicate(text.strip(), voice, rate=rate_str, volume=volume_str, pitch=pitch_str)
    async for chunk in communicate.stream():
        if chunk["type"] == "audio":
            result.write(chunk["data"])
        elif chunk["type"] == "WordBoundary":
            extracted = {
                "start": chunk["offset"] / 10**7,
                "duration": chunk["duration"] / 10**7,
                "text": chunk["text"],
            }
            meta_info.append(extracted)
            # print(f"WordBoundary: {extracted}")
    result.seek(0)
    # decoded_chunk = AudioSegment.from_mp3(temp_chunk)
    # try except: decoded_chunk = AudioSegment.silent(0, 24000)
    # return decoded_chunk.raw_data
    # with Path("asd.mp3").open("wb") as f:
    #     f.write(result.getvalue())
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
    asyncio.run(main())
