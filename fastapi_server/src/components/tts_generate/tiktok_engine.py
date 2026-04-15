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
from loguru import logger
from mutagen.mp3 import MP3

from schemas.tts import VoiceInfo

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
        engine="tiktok",
        internal_name="en_us_ghostface",
        gender="Unknown",
        locale="en-us",
        label="Ghost Face",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_chewbacca",
        gender="Unknown",
        locale="en-us",
        label="Chewbacca",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_c3po",
        gender="Unknown",
        locale="en-us",
        label="C-3PO",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_stitch",
        gender="Unknown",
        locale="en-us",
        label="Stitch",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_stormtrooper",
        gender="Unknown",
        locale="en-us",
        label="Stormtrooper",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_rocket",
        gender="Unknown",
        locale="en-us",
        label="Rocket",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_madam_leota",
        gender="Female",
        locale="en-us",
        label="Madame Leota",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_ghosthost",
        gender="Male",
        locale="en-us",
        label="Ghost Host",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_pirate",
        gender="Male",
        locale="en-us",
        label="Pirate",
    ),
    # English Voices
    VoiceInfo(
        engine="tiktok",
        internal_name="en_au_001",
        gender="Female",
        locale="en-au",
        label="Australian Female",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_au_002",
        gender="Male",
        locale="en-au",
        label="Australian Male",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_uk_001",
        gender="Male",
        locale="en-uk",
        label="UK Male 1",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_uk_003",
        gender="Male",
        locale="en-uk",
        label="UK Male 2",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_001",
        gender="Female",
        locale="en-us",
        label="US Female 1",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_002",
        gender="Female",
        locale="en-us",
        label="US Female 2",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_006",
        gender="Male",
        locale="en-us",
        label="US Male 1",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_007",
        gender="Male",
        locale="en-us",
        label="US Male 2",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_009",
        gender="Male",
        locale="en-us",
        label="US Male 3",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_us_010",
        gender="Male",
        locale="en-us",
        label="US Male 4",
    ),
    # English Voices (Other)
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_narration",
        gender="Male",
        locale="en-us",
        label="Narrator",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_funny",
        gender="Male",
        locale="en-us",
        label="Wacky",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_emotional",
        gender="Female",
        locale="en-us",
        label="Peaceful",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_cody",
        gender="Male",
        locale="en-us",
        label="Serious",
    ),
    # Western European
    VoiceInfo(
        engine="tiktok",
        internal_name="fr_001",
        gender="Male",
        locale="fr-fr",
        label="French Male 1",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="fr_002",
        gender="Male",
        locale="fr-fr",
        label="French Male 2",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="de_001",
        gender="Female",
        locale="de-de",
        label="German Female",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="de_002",
        gender="Male",
        locale="de-de",
        label="German Male",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="es_002",
        gender="Male",
        locale="es-es",
        label="Spanish Male",
    ),
    # South American
    VoiceInfo(
        engine="tiktok",
        internal_name="es_mx_002",
        gender="Male",
        locale="es-mx",
        label="Spanish MX Male",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="br_001",
        gender="Female",
        locale="pt-br",
        label="Portuguese BR Female 1",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="br_003",
        gender="Female",
        locale="pt-br",
        label="Portuguese BR Female 2",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="br_004",
        gender="Female",
        locale="pt-br",
        label="Portuguese BR Female 3",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="br_005",
        gender="Male",
        locale="pt-br",
        label="Portuguese BR Male",
    ),
    # Asian
    VoiceInfo(
        engine="tiktok",
        internal_name="id_001",
        gender="Female",
        locale="id-id",
        label="Indonesian Female",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="jp_001",
        gender="Female",
        locale="ja-jp",
        label="Japanese Female 1",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="jp_003",
        gender="Female",
        locale="ja-jp",
        label="Japanese Female 2",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="jp_005",
        gender="Female",
        locale="ja-jp",
        label="Japanese Female 3",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="jp_006",
        gender="Male",
        locale="ja-jp",
        label="Japanese Male",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="kr_002",
        gender="Male",
        locale="ko-kr",
        label="Korean Male 1",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="kr_003",
        gender="Female",
        locale="ko-kr",
        label="Korean Female",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="kr_004",
        gender="Male",
        locale="ko-kr",
        label="Korean Male 2",
    ),
    # Vocals (Singing Voices)
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_f08_salut_damour",
        gender="Female",
        locale="en-us",
        label="Alto",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_m03_lobby",
        gender="Male",
        locale="en-us",
        label="Tenor",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_m03_sunshine_soon",
        gender="Male",
        locale="en-us",
        label="Sunshine Soon",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_f08_warmy_breeze",
        gender="Female",
        locale="en-us",
        label="Warmy Breeze",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_ht_f08_glorious",
        gender="Female",
        locale="en-us",
        label="Glorious",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_sing_funny_it_goes_up",
        gender="Male",
        locale="en-us",
        label="It Goes Up",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_m2_xhxs_m03_silly",
        gender="Male",
        locale="en-us",
        label="Chipmunk",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_ht_f08_wonderful_world",
        gender="Female",
        locale="en-us",
        label="Wonderful World",
    ),
    # Character Voices
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_samc",
        gender="Female",
        locale="en-us",
        label="Empathetic",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_jarvis",
        gender="Male",
        locale="en-us",
        label="Alfred",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_betty",
        gender="Female",
        locale="en-us",
        label="Bae",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_santa_narration",
        gender="Male",
        locale="en-us",
        label="Beauty Guru",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_santa",
        gender="Male",
        locale="en-us",
        label="Santa",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_santa_effect",
        gender="Male",
        locale="en-us",
        label="Santa WO Effect",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_richgirl",
        gender="Female",
        locale="en-us",
        label="Bestie",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_cupid",
        gender="Male",
        locale="en-us",
        label="Cupid",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_ukneighbor",
        gender="Male",
        locale="en-uk",
        label="Lord Cringe",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_wizard",
        gender="Male",
        locale="en-us",
        label="Magician",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_trevor",
        gender="Male",
        locale="en-us",
        label="Marty",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_shenna",
        gender="Female",
        locale="en-us",
        label="Debutante",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_makeup",
        gender="Female",
        locale="en-us",
        label="Author",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_grandma",
        gender="Female",
        locale="en-us",
        label="Grandma",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_grinch",
        gender="Male",
        locale="en-us",
        label="Trickster Grinch",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_deadpool",
        gender="Male",
        locale="en-us",
        label="Good Guy Deadpool",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_ukbutler",
        gender="Male",
        locale="en-uk",
        label="Meticulous",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_petercullen",
        gender="Male",
        locale="en-us",
        label="Optimus Prime",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_pansino",
        gender="Female",
        locale="en-us",
        label="Varsity",
    ),
    # Singing Voices (Additional)
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_sing_deep_jingle",
        gender="Male",
        locale="en-us",
        label="Song Caroler",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_m03_classical",
        gender="Male",
        locale="en-us",
        label="Song Classic Electric",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_m2_xhxs_m03_christmas",
        gender="Male",
        locale="en-us",
        label="Song Cozy",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_ht_f08_halloween",
        gender="Female",
        locale="en-us",
        label="Song Halloween",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_ht_f08_newyear",
        gender="Female",
        locale="en-us",
        label="Song NYE 2023",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_male_sing_funny_thanksgiving",
        gender="Male",
        locale="en-us",
        label="Song Thanksgiving",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="en_female_f08_twinkle",
        gender="Female",
        locale="en-us",
        label="Song Pop Lullaby",
    ),
    # Additional
    VoiceInfo(
        engine="tiktok",
        internal_name="it_male_m18",
        gender="Male",
        locale="it-it",
        label="Italian Male",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="es_male_m3",
        gender="Male",
        locale="es-es",
        label="Spanish Male Julio",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="es_female_f6",
        gender="Female",
        locale="es-es",
        label="Spanish Female Alejandra",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="es_female_fp1",
        gender="Female",
        locale="es-mx",
        label="Spanish Female Mariana",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="es_mx_male_transformer",
        gender="Male",
        locale="es-mx",
        label="MX Optimus Prime",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="pt_female_lhays",
        gender="Female",
        locale="pt-br",
        label="Portuguese Lhays Macedo",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="pt_female_laizza",
        gender="Female",
        locale="pt-br",
        label="Portuguese Laizza",
    ),
    VoiceInfo(
        engine="tiktok",
        internal_name="pt_male_transformer",
        gender="Male",
        locale="pt-br",
        label="PT Optimus Prime",
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
            logger.info(voice)
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
        display = voice.label or voice.internal_name
        logger.info(f"  {display} ({voice.gender}, {voice.locale}) - {voice.label}")

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
