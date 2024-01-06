from __future__ import annotations

import asyncio
import base64
import enum
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Annotated

import aiohttp
from litestar import Controller, get, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Template
from litestar.template.config import TemplateConfig

template_config = TemplateConfig(engine=JinjaTemplateEngine, directory="templates")


# https://github.com/oscie57/tiktok-voice/issues/1
class Voices(enum.Enum):
    # DISNEY VOICES
    GHOST_FACE = "en_us_ghostface"
    CHEWBACCA = "en_us_chewbacca"
    C3PO = "en_us_c3po"
    STITCH = "en_us_stitch"
    STORMTROOPER = "en_us_stormtrooper"
    ROCKET = "en_us_rocket"
    # ENGLISH VOICES
    ENGLISH_AU_FEMALE = "en_au_001"
    ENGLISH_AU_MALE = "en_au_002"
    ENGLISH_UK_MALE_1 = "en_uk_001"
    ENGLISH_UK_MALE_2 = "en_uk_003"
    ENGLISH_US_FEMALE_1 = "en_us_001"
    ENGLISH_US_FEMALE_2 = "en_us_002"
    ENGLISH_US_MALE_1 = "en_us_006"
    ENGLISH_US_MALE_2 = "en_us_007"
    ENGLISH_US_MALE_3 = "en_us_009"
    ENGLISH_US_MALE_4 = "en_us_010"
    # EUROPE VOICES
    FRENCH_MALE_1 = "fr_001"
    FRENCH_MALE_2 = "fr_002"
    GERMAN_FEMALE = "de_001"
    GERMAN_MALE = "de_002"
    SPANISH_MALE = "es_002"
    # AMERICA VOICES
    SPANISH_MX_MALE = "es_mx_002"
    PORTUGUESE_BR_FEMALE_1 = "br_001"
    PORTUGUESE_BR_FEMALE_2 = "br_003"
    PORTUGUESE_BR_FEMALE_3 = "br_004"
    PORTUGUESE_BR_MALE = "br_005"
    # ASIA VOICES
    INDONESIAN_FEMALE = "id_001"
    JAPANESE_FEMALE_1 = "jp_001"
    JAPANESE_FEMALE_2 = "jp_003"
    JAPANESE_FEMALE_3 = "jp_005"
    JAPANESE_MALE = "jp_006"
    KOREAN_MALE_1 = "kr_002"
    KOREAN_FEMALE = "kr_003"
    KOREAN_MALE_2 = "kr_004"
    # SINGING VOICES
    SONG_CAROLER = "en_male_sing_deep_jingle"
    SONG_CLASSIC_ELECTRIC = "en_male_m03_classical"
    SONG_COTTAGECORE = "en_female_f08_salut_damour"
    SONG_COZY = "en_male_m2_xhxs_m03_christmas"
    SONG_WARMY_BREEZE = "en_female_f08_warmy_breeze"
    SONG_HALLOWEEN = "en_female_ht_f08_halloween"
    SONG_EUPHORIC = "en_female_ht_f08_glorious"
    SONG_HYPETRAIN = "en_male_sing_funny_it_goes_up"
    SONG_TENOR = "en_male_m03_lobby"
    SONG_MELODRAMA = "en_female_ht_f08_wonderful_world"
    SONG_NYE_2023 = "en_female_ht_f08_newyear"
    SONG_THANKSGIVING = "en_male_sing_funny_thanksgiving"
    SONG_SUNSHINE_SOON = "en_male_m03_sunshine_soon"
    SONG_LULLABY = "en_female_f08_twinkle"
    SONG_QUIRKY = "en_male_m2_xhxs_m03_silly"
    # OTHER
    NARRATOR = "en_male_narration"
    WACKY = "en_male_funny"
    PEACEFUL = "en_female_emotional"
    GRANDMA = "en_female_grandma"
    GRINCH = "en_male_grinch"
    OPTIMUS_PRIME = "es_female_fp1"


async def generate_tts(voice: Voices, text: str) -> tuple[str, float]:
    async with aiohttp.ClientSession() as s:
        headers = {
            "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",  # noqa: E501
            "Cookie": f"sessionid={os.getenv('TIKTOK_SESSION_ID')}",
        }
        url = f"https://api16-normal-c-useast2a.tiktokv.com/media/api/text/speech/invoke/?text_speaker={voice.value}&req_text={text}&speaker_map_type=0&aid=1233"
        r = await s.post(url, headers=headers)
        data = await r.json()

        status_code: int = data["status_code"]
        # message: str = data["message"]
        # status_msg: str = data["status_msg"]
        assert status_code == 0, f"{status_code=}"

        duration: str = data["data"]["duration"]
        duration_seconds: float = int(duration) / 60

        return data["data"]["v_str"], duration_seconds
        # b64data = base64.b64decode(data["data"]["v_str"])
        # return b64data, duration_seconds


class MyTTSRoute(Controller):
    path = "/tts"
    VOICES_LIST: list[str] = [v.name for v in Voices]

    @get("/")
    async def index(self) -> Template:
        # Return an initial index.html that can play tts from input form
        return Template(template_name="tts/index.html", context={
            "voices": self.VOICES_LIST,
            "mp3_b64_data": "",
        })

    @dataclass
    class TTSData:
        tts_voice: str
        tts_text: str

    @post("/generate_mp3")
    async def generate_mp3(
        self,
        data: Annotated[TTSData, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        mp3_data, _ = await generate_tts(Voices[data.tts_voice], data.tts_text)
        # TODO Handle status code / errors
        return Template(template_name="tts/new_audio.html", context={
            "mp3_b64_data": mp3_data,
        })

    @get("/with-name")
    async def tts_with_name(self) -> str:
        # TODO Websocket, join a twitch channel if websocket connects
        # Read name: "burnysc2 says: text"
        return "Hello world!"

    @get("/without-name")
    async def tts_without_name(self) -> str:
        # TODO Websocket, join a twitch channel if websocket connects
        # Dont read name: "text"
        return "Hello world!"

    @get("/pdf")
    async def tts_from_pdf(self) -> str:
        # TODO Upload file, read chapters, select which chapters to extract as .mp3
        return "Hello world!"


async def main():
    # Log in to tiktok, check cookies, use value stored in 'sessionid'
    text_speaker: Voices = Voices.SONG_TENOR
    req_text = "test text"
    b64data, duration_seconds = await generate_tts(text_speaker, req_text)

    b64data = base64.b64decode(b64data)
    path = Path("temp.mp3")
    with path.open("wb") as f:
        f.write(b64data)


if __name__ == "__main__":
    asyncio.run(main())
