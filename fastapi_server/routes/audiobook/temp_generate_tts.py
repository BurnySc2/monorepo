import asyncio
import io

import edge_tts

# from pydub import AudioSegment


async def get_supported_voices() -> dict[str, str]:
    # TODO Cache result for at least 1h, maybe a day
    voices = await edge_tts.list_voices()
    result = {voice["ShortName"]: voice["Locale"] for voice in sorted(voices, key=lambda voice: voice["ShortName"])}
    return result


async def generate_text_to_speech(
    text: str,
    voice: str,
    rate: str = "+0%",
    volume: str = "+0%",
    pitch: str = "+0Hz",
) -> io.BytesIO:
    result = io.BytesIO()
    meta_info = []
    communicate = edge_tts.Communicate(text.strip(), voice, rate=rate, volume=volume, pitch=pitch)
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
    voices = await get_supported_voices()
    TEXT = "Hello World! This is one sentence. What is the second sentence?"
    TEXT = """
Title: The Enduring Legacy of\nStarCraft II: A Saga of Strategy, Esports, and Innovation

Introduction:

Since its release in 2010, StarCraft II\nhas etched its place in gaming history as one of the most iconic real-time strategy (RTS) games of all time. Developed by Blizzard\nEntertainment, StarCraft II is the\nsequel to the original StarCraft, a game\nthat revolutionized the RTS genre in the late 1990s. In this essay, we will delve into the multifaceted world of StarCraft II, exploring its gameplay mechanics, its impact on esports, its enduring legacy, and its contributions to the gaming industry.
"""
    VOICE = "en-GB-SoniaNeural"
    result = await generate_text_to_speech(TEXT, VOICE)
    # with Path("asd.mp3").open("wb") as f:
    #     f.write(result.getvalue())


if __name__ == "__main__":
    asyncio.run(main())
