"""
TikTok TTS - Unofficial TikTok voice API using session authentication.

Get sessionid via "sessionid" cookie after logging in on tiktok.
With cookie name "store-idc" you can find the server name your sessionid works with.

https://github.com/oscie57/tiktok-voice/issues/1
https://github.com/oscie57/tiktok-voice/wiki/Voice-Codes
"""

from __future__ import annotations

import base64
import os
from io import BytesIO

import httpx
from cachetools import TTLCache
from mutagen.mp3 import MP3

from components.tts_generate._voice_info import VoiceInfo

_voice_cache: TTLCache = TTLCache(maxsize=1, ttl=300)

# Cache: (voice_code, text) -> (audio_bytes, duration)
_audio_cache: TTLCache = TTLCache(maxsize=1000, ttl=3600)

SESSION_ID = os.getenv("TIKTOK_SESSION_ID")

API_DOMAINS = [
    "https://api16-normal-c-useast2a.tiktokv.com",
]
API_PATH = "/media/api/text/speech/invoke/"

VOICES = [
    VoiceInfo(
        name="en_au_001",
        short_name="Eddie",
        gender="Female",
        locale="en-au",
        language="English (AU)",
        description="Australian Female - Eddie",
    ),
    VoiceInfo(
        name="en_au_002",
        short_name="Alex",
        gender="Male",
        locale="en-au",
        language="English (AU)",
        description="Australian Male - Smooth Alex",
    ),
    VoiceInfo(
        name="en_uk_001",
        short_name="UK Male 1",
        gender="Male",
        locale="en-uk",
        language="English (UK)",
        description="UK Male 1",
    ),
    VoiceInfo(
        name="en_uk_003",
        short_name="UK Male 2",
        gender="Male",
        locale="en-uk",
        language="English (UK)",
        description="UK Male 2",
    ),
    VoiceInfo(
        name="en_us_002",
        short_name="Jessie",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="US Female - Jessie",
    ),
    VoiceInfo(
        name="en_us_006",
        short_name="Joey",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male - Joey",
    ),
    VoiceInfo(
        name="en_us_007",
        short_name="Professor",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male - Professor",
    ),
    VoiceInfo(
        name="en_us_009",
        short_name="Scientist",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male - Scientist",
    ),
    VoiceInfo(
        name="en_us_010",
        short_name="Confidence",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male - Confidence",
    ),
    VoiceInfo(
        name="en_us_ghostface",
        short_name="Ghost Face",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Ghost Face (Scream)",
    ),
    VoiceInfo(
        name="en_us_chewbacca",
        short_name="Chewbacca",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Chewbacca",
    ),
    VoiceInfo(
        name="en_us_c3po",
        short_name="C-3PO",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="C-3PO",
    ),
    VoiceInfo(
        name="en_us_stitch",
        short_name="Stitch",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Stitch",
    ),
    VoiceInfo(
        name="en_us_stormtrooper",
        short_name="Stormtrooper",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Stormtrooper",
    ),
    VoiceInfo(
        name="en_us_rocket",
        short_name="Rocket",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Rocket (Guardians of the Galaxy)",
    ),
    VoiceInfo(
        name="fr_001",
        short_name="French Male 1",
        gender="Male",
        locale="fr-fr",
        language="French",
        description="French Male 1",
    ),
    VoiceInfo(
        name="fr_002",
        short_name="French Male 2",
        gender="Male",
        locale="fr-fr",
        language="French",
        description="French Male 2",
    ),
    VoiceInfo(
        name="de_001",
        short_name="German Female",
        gender="Female",
        locale="de-de",
        language="German",
        description="German Female",
    ),
    VoiceInfo(
        name="de_002",
        short_name="German Male",
        gender="Male",
        locale="de-de",
        language="German",
        description="German Male",
    ),
    VoiceInfo(
        name="es_002",
        short_name="Spanish Male",
        gender="Male",
        locale="es-es",
        language="Spanish",
        description="Spanish Male",
    ),
    VoiceInfo(
        name="es_male_m3",
        short_name="Julio",
        gender="Male",
        locale="es-es",
        language="Spanish",
        description="Spanish Male - Julio",
    ),
    VoiceInfo(
        name="es_female_f6",
        short_name="Alejandra",
        gender="Female",
        locale="es-es",
        language="Spanish",
        description="Spanish Female - Alejandra",
    ),
    VoiceInfo(
        name="es_female_fp1",
        short_name="Mariana",
        gender="Female",
        locale="es-es",
        language="Spanish",
        description="Spanish Female - Mariana",
    ),
    VoiceInfo(
        name="jp_001",
        short_name="Japanese Female 1",
        gender="Female",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Female 1",
    ),
    VoiceInfo(
        name="jp_003",
        short_name="Japanese Female 2",
        gender="Female",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Female 2",
    ),
    VoiceInfo(
        name="jp_005",
        short_name="Japanese Female 3",
        gender="Female",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Female 3",
    ),
    VoiceInfo(
        name="jp_006",
        short_name="Japanese Male",
        gender="Male",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Male",
    ),
    VoiceInfo(
        name="kr_002",
        short_name="Korean Male 1",
        gender="Male",
        locale="ko-kr",
        language="Korean",
        description="Korean Male 1",
    ),
    VoiceInfo(
        name="kr_003",
        short_name="Korean Female",
        gender="Female",
        locale="ko-kr",
        language="Korean",
        description="Korean Female",
    ),
    VoiceInfo(
        name="kr_004",
        short_name="Korean Male 2",
        gender="Male",
        locale="ko-kr",
        language="Korean",
        description="Korean Male 2",
    ),
]


async def list_voices_async() -> list[VoiceInfo]:
    """List all available TikTok TTS voices."""
    return VOICES


async def generate_audio_async(
    voice: str,
    text: str,
) -> tuple[bytes, float]:
    """
    Generate audio using TikTok TTS.

    Args:
        voice: Voice code (e.g., "en_us_002")
        text: Text to synthesize

    Returns:
        Tuple of (audio_bytes, duration_seconds)
    """
    key = (voice, text)
    if key in _audio_cache:
        return _audio_cache[key]

    headers = {
        "User-Agent": (
            "com.zhiliaoapp.musically/2022600030 "
            "(Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)"
        ),
        "Cookie": f"sessionid={SESSION_ID}",
    }

    data = {}
    status_code = 1
    async with httpx.AsyncClient() as client:
        for domain in API_DOMAINS:
            url = f"{domain}{API_PATH}?text_speaker={voice}&req_text={text}&speaker_map_type=0&aid=1233"
            response = await client.post(url, headers=headers)
            if response.is_error:
                continue
            data = response.json()
            status_code = data.get("status_code", 1)
            if status_code == 0:
                break

    if status_code != 0:
        raise RuntimeError(f"TikTok TTS failed: {data}")

    b64data = data["data"]["v_str"]
    audio_bytes = base64.b64decode(b64data)

    mp3_info = MP3(BytesIO(audio_bytes))
    duration = mp3_info.info.length

    _audio_cache[key] = (audio_bytes, duration)

    return audio_bytes, duration


async def main() -> None:
    """Run to list all voices and generate a sample MP3."""
    from pathlib import Path

    from loguru import logger

    voices = await list_voices_async()
    logger.info(f"Found {len(voices)} voices:")
    for voice in voices:
        display = voice.short_name or voice.name
        logger.info(f"  {display} ({voice.gender}, {voice.locale}) - {voice.description}")

    sample_voice = "en_us_002"
    sample_text = "Hello from TikTok TTS! This is a test."
    output_path = Path(__file__).parent / "sample_tiktok.mp3"

    logger.info(f"Generating sample audio with voice '{sample_voice}'...")
    audio_bytes, duration = await generate_audio_async(sample_voice, sample_text)
    with output_path.open("wb") as f:
        f.write(audio_bytes)
    logger.success(f"Audio saved to: {output_path} (duration: {duration:.1f}s)")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
