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
    # Disney Voices
    VoiceInfo(
        name="en_us_ghostface",
        short_name="ghost_face",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Ghost Face (Scream)",
    ),
    VoiceInfo(
        name="en_us_chewbacca",
        short_name="chewbacca",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Chewbacca",
    ),
    VoiceInfo(
        name="en_us_c3po",
        short_name="c3po",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="C-3PO",
    ),
    VoiceInfo(
        name="en_us_stitch",
        short_name="stitch",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Stitch",
    ),
    VoiceInfo(
        name="en_us_stormtrooper",
        short_name="stormtrooper",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Stormtrooper",
    ),
    VoiceInfo(
        name="en_us_rocket",
        short_name="rocket",
        gender="Unknown",
        locale="en-us",
        language="English (US)",
        description="Rocket (Guardians of the Galaxy)",
    ),
    VoiceInfo(
        name="en_female_madam_leota",
        short_name="madam_leota",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="Madame Leota",
    ),
    VoiceInfo(
        name="en_male_ghosthost",
        short_name="ghost_host",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Ghost Host",
    ),
    VoiceInfo(
        name="en_male_pirate",
        short_name="pirate",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Pirate",
    ),
    # English Voices
    VoiceInfo(
        name="en_au_001",
        short_name="australian_female",
        gender="Female",
        locale="en-au",
        language="English (AU)",
        description="Australian Female",
    ),
    VoiceInfo(
        name="en_au_002",
        short_name="australian_male",
        gender="Male",
        locale="en-au",
        language="English (AU)",
        description="Australian Male",
    ),
    VoiceInfo(
        name="en_uk_001",
        short_name="uk_male_1",
        gender="Male",
        locale="en-uk",
        language="English (UK)",
        description="UK Male 1",
    ),
    VoiceInfo(
        name="en_uk_003",
        short_name="uk_male_2",
        gender="Male",
        locale="en-uk",
        language="English (UK)",
        description="UK Male 2",
    ),
    VoiceInfo(
        name="en_us_001",
        short_name="us_female_1",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="US Female 1",
    ),
    VoiceInfo(
        name="en_us_002",
        short_name="us_female_2",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="US Female 2",
    ),
    VoiceInfo(
        name="en_us_006",
        short_name="us_male_1",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male 1",
    ),
    VoiceInfo(
        name="en_us_007",
        short_name="us_male_2",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male 2",
    ),
    VoiceInfo(
        name="en_us_009",
        short_name="us_male_3",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male 3",
    ),
    VoiceInfo(
        name="en_us_010",
        short_name="us_male_4",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="US Male 4",
    ),
    # English Voices (Other)
    VoiceInfo(
        name="en_male_narration",
        short_name="narrator",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Narrator",
    ),
    VoiceInfo(
        name="en_male_funny",
        short_name="wacky",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Wacky",
    ),
    VoiceInfo(
        name="en_female_emotional",
        short_name="peaceful",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="Peaceful",
    ),
    VoiceInfo(
        name="en_male_cody",
        short_name="serious",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Serious",
    ),
    # Western European
    VoiceInfo(
        name="fr_001",
        short_name="french_male_1",
        gender="Male",
        locale="fr-fr",
        language="French",
        description="French Male 1",
    ),
    VoiceInfo(
        name="fr_002",
        short_name="french_male_2",
        gender="Male",
        locale="fr-fr",
        language="French",
        description="French Male 2",
    ),
    VoiceInfo(
        name="de_001",
        short_name="german_female",
        gender="Female",
        locale="de-de",
        language="German",
        description="German Female",
    ),
    VoiceInfo(
        name="de_002",
        short_name="german_male",
        gender="Male",
        locale="de-de",
        language="German",
        description="German Male",
    ),
    VoiceInfo(
        name="es_002",
        short_name="spanish_male",
        gender="Male",
        locale="es-es",
        language="Spanish",
        description="Spanish Male",
    ),
    # South American Languages
    VoiceInfo(
        name="es_mx_002",
        short_name="spanish_mx_male",
        gender="Male",
        locale="es-mx",
        language="Spanish (MX)",
        description="Spanish MX Male",
    ),
    VoiceInfo(
        name="br_001",
        short_name="portuguese_br_female_1",
        gender="Female",
        locale="pt-br",
        language="Portuguese (BR)",
        description="Portuguese BR Female 1",
    ),
    VoiceInfo(
        name="br_003",
        short_name="portuguese_br_female_2",
        gender="Female",
        locale="pt-br",
        language="Portuguese (BR)",
        description="Portuguese BR Female 2",
    ),
    VoiceInfo(
        name="br_004",
        short_name="portuguese_br_female_3",
        gender="Female",
        locale="pt-br",
        language="Portuguese (BR)",
        description="Portuguese BR Female 3",
    ),
    VoiceInfo(
        name="br_005",
        short_name="portuguese_br_male",
        gender="Male",
        locale="pt-br",
        language="Portuguese (BR)",
        description="Portuguese BR Male",
    ),
    # Asian Languages
    VoiceInfo(
        name="id_001",
        short_name="indonesian_female",
        gender="Female",
        locale="id-id",
        language="Indonesian",
        description="Indonesian Female",
    ),
    VoiceInfo(
        name="jp_001",
        short_name="japanese_female_1",
        gender="Female",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Female 1",
    ),
    VoiceInfo(
        name="jp_003",
        short_name="japanese_female_2",
        gender="Female",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Female 2",
    ),
    VoiceInfo(
        name="jp_005",
        short_name="japanese_female_3",
        gender="Female",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Female 3",
    ),
    VoiceInfo(
        name="jp_006",
        short_name="japanese_male",
        gender="Male",
        locale="ja-jp",
        language="Japanese",
        description="Japanese Male",
    ),
    VoiceInfo(
        name="kr_002",
        short_name="korean_male_1",
        gender="Male",
        locale="ko-kr",
        language="Korean",
        description="Korean Male 1",
    ),
    VoiceInfo(
        name="kr_003",
        short_name="korean_female",
        gender="Female",
        locale="ko-kr",
        language="Korean",
        description="Korean Female",
    ),
    VoiceInfo(
        name="kr_004",
        short_name="korean_male_2",
        gender="Male",
        locale="ko-kr",
        language="Korean",
        description="Korean Male 2",
    ),
    # Vocals (Singing Voices)
    VoiceInfo(
        name="en_female_f08_salut_damour",
        short_name="alto",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="Alto",
    ),
    VoiceInfo(
        name="en_male_m03_lobby",
        short_name="tenor",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Tenor",
    ),
    VoiceInfo(
        name="en_male_m03_sunshine_soon",
        short_name="sunshine_soon",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Sunshine Soon",
    ),
    VoiceInfo(
        name="en_female_f08_warmy_breeze",
        short_name="warmy_breeze",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="Warmy Breeze",
    ),
    VoiceInfo(
        name="en_female_ht_f08_glorious",
        short_name="glorious",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="Glorious",
    ),
    VoiceInfo(
        name="en_male_sing_funny_it_goes_up",
        short_name="it_goes_up",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="It Goes Up",
    ),
    VoiceInfo(
        name="en_male_m2_xhxs_m03_silly",
        short_name="chipmunk",
        gender="Male",
        locale="en-us",
        language="English (US)",
        description="Chipmunk",
    ),
    VoiceInfo(
        name="en_female_ht_f08_wonderful_world",
        short_name="wonderful_world",
        gender="Female",
        locale="en-us",
        language="English (US)",
        description="Wonderful World",
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
