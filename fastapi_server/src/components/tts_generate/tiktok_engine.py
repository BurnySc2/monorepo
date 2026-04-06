"""
TikTok TTS - Unofficial TikTok voice API using session authentication.
Get sessionid via "sessionid" cookie after logging in on TikTok.
"""

from __future__ import annotations

import base64
import os
from collections import OrderedDict
from dataclasses import dataclass
from io import BytesIO

import httpx
from mutagen.mp3 import MP3


@dataclass
class VoiceInfo:
    """Information about a voice."""
    name: str
    code: str
    language: str
    description: str


VOICES = [
    # English
    VoiceInfo("ENGLISH_AU_FEMALE_METRO_EDDIE", "en_au_001", "English (AU)", "Australian Female - Eddie"),
    VoiceInfo("ENGLISH_AU_MALE_SMOOTH_ALEX", "en_au_002", "English (AU)", "Australian Male - Smooth Alex"),
    VoiceInfo("ENGLISH_UK_MALE_1", "en_uk_001", "English (UK)", "UK Male 1"),
    VoiceInfo("ENGLISH_UK_MALE_2", "en_uk_003", "English (UK)", "UK Male 2"),
    VoiceInfo("ENGLISH_US_FEMALE_JESSIE", "en_us_002", "English (US)", "US Female - Jessie"),
    VoiceInfo("ENGLISH_US_MALE_JOEY", "en_us_006", "English (US)", "US Male - Joey"),
    VoiceInfo("ENGLISH_US_MALE_PROFESSOR", "en_us_007", "English (US)", "US Male - Professor"),
    VoiceInfo("ENGLISH_US_MALE_SCIENTIST", "en_us_009", "English (US)", "US Male - Scientist"),
    VoiceInfo("ENGLISH_US_MALE_CONFIDENCE", "en_us_010", "English (US)", "US Male - Confidence"),
    # Disney voices
    VoiceInfo("GHOST_FACE", "en_us_ghostface", "English (US)", "Ghost Face (Scream)"),
    VoiceInfo("CHEWBACCA", "en_us_chewbacca", "English (US)", "Chewbacca"),
    VoiceInfo("C3PO", "en_us_c3po", "English (US)", "C-3PO"),
    VoiceInfo("STITCH", "en_us_stitch", "English (US)", "Stitch"),
    VoiceInfo("STORMTROOPER", "en_us_stormtrooper", "English (US)", "Stormtrooper"),
    VoiceInfo("ROCKET", "en_us_rocket", "English (US)", "Rocket (Guardians of the Galaxy)"),
    # French
    VoiceInfo("FRENCH_MALE_1", "fr_001", "French", "French Male 1"),
    VoiceInfo("FRENCH_MALE_2", "fr_002", "French", "French Male 2"),
    # German
    VoiceInfo("GERMAN_FEMALE", "de_001", "German", "German Female"),
    VoiceInfo("GERMAN_MALE", "de_002", "German", "German Male"),
    # Spanish
    VoiceInfo("SPANISH_MALE", "es_002", "Spanish", "Spanish Male"),
    VoiceInfo("SPANISH_MALE_JULIO", "es_male_m3", "Spanish", "Spanish Male - Julio"),
    VoiceInfo("SPANISH_FEMALE_ALEJANDRA", "es_female_f6", "Spanish", "Spanish Female - Alejandra"),
    VoiceInfo("SPANISH_FEMALE_MARIANA", "es_female_fp1", "Spanish", "Spanish Female - Mariana"),
    # Japanese
    VoiceInfo("JAPANESE_FEMALE_1", "jp_001", "Japanese", "Japanese Female 1"),
    VoiceInfo("JAPANESE_FEMALE_2", "jp_003", "Japanese", "Japanese Female 2"),
    VoiceInfo("JAPANESE_FEMALE_3", "jp_005", "Japanese", "Japanese Female 3"),
    VoiceInfo("JAPANESE_MALE", "jp_006", "Japanese", "Japanese Male"),
    # Korean
    VoiceInfo("KOREAN_MALE_1", "kr_002", "Korean", "Korean Male 1"),
    VoiceInfo("KOREAN_FEMALE", "kr_003", "Korean", "Korean Female"),
    VoiceInfo("KOREAN_MALE_2", "kr_004", "Korean", "Korean Male 2"),
]

SESSION_ID = os.getenv("TIKTOK_SESSION_ID")
CACHE_LIMIT = 1000

# Cache: (voice_code, text) -> (audio_path, duration)
_tts_cache: OrderedDict[tuple[str, str], tuple[str, float]] = OrderedDict()

# API domains for TikTok TTS
API_DOMAINS = [
    "https://api16-normal-c-useast2a.tiktokv.com",
]
API_PATH = "/media/api/text/speech/invoke/"


async def list_voices_async() -> list[VoiceInfo]:
    """List all available TikTok TTS voices."""
    return VOICES


async def generate_audio_async(
    voice: str,
    text: str,
    output_path: str | None = None,
) -> tuple[str, float]:
    """
    Generate audio using TikTok TTS.

    Args:
        voice: Voice code (e.g., "en_us_002")
        text: Text to synthesize
        output_path: Optional output path. If None, a temp file is created.

    Returns:
        Tuple of (output_path, duration_seconds)
    """
    if output_path is None:
        import tempfile
        output_path = tempfile.mktemp(suffix=".mp3")

    key = (voice, text)
    if key in _tts_cache:
        # Refresh cache order
        _tts_cache[key] = _tts_cache.pop(key)
        cached_path, cached_duration = _tts_cache[key]
        # Copy cached file to requested output
        import shutil
        shutil.copy(cached_path, output_path)
        return output_path, cached_duration

    headers = {
        "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",
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

    # Decode base64 audio
    b64data = data["data"]["v_str"]
    b64data_decoded = base64.b64decode(b64data)
    audio_stream = BytesIO(b64data_decoded)

    # Get duration
    mp3_info = MP3(audio_stream)
    duration = mp3_info.info.length
    audio_stream.seek(0)

    # Write to output file
    with open(output_path, "wb") as f:
        f.write(b64data_decoded)

    # Update cache
    if len(_tts_cache) > CACHE_LIMIT:
        _tts_cache.popitem(last=False)
    _tts_cache[key] = (output_path, duration)

    return output_path, duration
