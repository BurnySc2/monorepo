"""
Generate voice via tiktok voice api.
Get sessionid via "sessionid" cookie after logging in on tiktok.
With cookie name "store-idc" you can find the server name your sessionid works with.
"""

from __future__ import annotations

import base64
from collections import OrderedDict
from io import BytesIO

import httpx
from mutagen.mp3 import MP3

from schemas.tts import Voices

SESSION_ID = None

CACHE_LIMIT = 1000
generated_tts_cache: OrderedDict[tuple[Voices, str], tuple[str, float]] = OrderedDict()

API_DOMAINS = list(
    {
        "https://api16-normal-c-useast2a.tiktokv.com",
    }
)
API_PATH = "/media/api/text/speech/invoke/"


async def generate_tts(voice: Voices, text: str) -> tuple[str, float]:
    key = (voice, text)
    if key in generated_tts_cache:
        generated_tts_cache[key] = generated_tts_cache.pop(key)
        return generated_tts_cache[key]

    async with httpx.AsyncClient() as client:
        headers = {
            "User-Agent": (
                "com.zhiliaoapp.musically/2022600030 "
                "(Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)"
            ),
            "Cookie": f"sessionid={SESSION_ID}",
        }

        data = {}
        status_code = 1
        for domain in API_DOMAINS:
            url = f"{domain}{API_PATH}?text_speaker={voice.value}&req_text={text}&speaker_map_type=0&aid=1233"
            response = await client.post(url, headers=headers)
            if response.is_error:
                continue
            data = response.json()

            status_code = data["status_code"]

            if status_code == 0:
                break

        assert status_code == 0, f"{data=}"

        if len(generated_tts_cache) > CACHE_LIMIT:
            generated_tts_cache.popitem(last=False)

        b64data = data["data"]["v_str"]
        b64data_decoded = base64.b64decode(b64data)
        data_io = BytesIO(b64data_decoded)
        mp3_info = MP3(data_io)
        real_duration_seconds = mp3_info.info.length

        generated_tts_cache[key] = b64data, real_duration_seconds
        return generated_tts_cache[key]


__all__ = ["Voices", "generate_tts"]
