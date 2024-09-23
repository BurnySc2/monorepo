from __future__ import annotations

import asyncio
import base64
import enum
import os
from collections import OrderedDict
from io import BytesIO
from pathlib import Path

import httpx
from mutagen.mp3 import MP3


# https://github.com/oscie57/tiktok-voice/issues/1
class Voices(enum.Enum):
    # ENGLISH VOICES
    ENGLISH_AU_FEMALE_METRO_EDDIE = "en_au_001"
    ENGLISH_AU_MALE_SMOOTH_ALEX = "en_au_002"
    ENGLISH_UK_MALE_1 = "en_uk_001"
    ENGLISH_UK_MALE_2 = "en_uk_003"
    ENGLISH_US_FEMALE_JESSIE = "en_us_002"
    ENGLISH_US_MALE_JOEY = "en_us_006"
    ENGLISH_US_MALE_PROFESSOR = "en_us_007"
    ENGLISH_US_MALE_SCIENTIST = "en_us_009"
    ENGLISH_US_MALE_CONFIDENCE = "en_us_010"
    # EUROPE VOICES
    FRENCH_MALE_1 = "fr_001"
    FRENCH_MALE_2 = "fr_002"
    GERMAN_FEMALE = "de_001"
    GERMAN_MALE = "de_002"
    ITALIAN_MALE = "it_male_m18"
    SPANISH_MALE = "es_002"
    SPANISH_MALE_JULIO = "es_male_m3"
    SPANISH_FEMALE_ALEJANDRA = "es_female_f6"
    SPANISH_FEMALE_MARIANA = "es_female_fp1"
    SPANISH_ALEX_WARM = "es_mx_002"
    MEXICAN_OPTIMUS_PRIME = "es_mx_male_transformer"
    PORTUGUESE_JULIA = "br_003"
    PORTUGUESE_ANA = "br_004"
    PORTUGUESE_LUCAS = "br_005"
    PORTUGUESE_LHAYS_MACEDO = "pt_female_lhays"
    PORTUGUESE_LAIZZA = "pt_female_laizza"
    PORTUGUESE_OPTIMUS_PRIME = "pt_male_transformer"
    # ASIA VOICES
    INDONESIAN_FEMALE = "id_001"
    JAPANESE_FEMALE_1 = "jp_001"
    JAPANESE_FEMALE_2 = "jp_003"
    JAPANESE_FEMALE_3 = "jp_005"
    JAPANESE_MALE = "jp_006"
    KOREAN_MALE_1 = "kr_002"
    KOREAN_FEMALE = "kr_003"
    KOREAN_MALE_2 = "kr_004"
    # DISNEY VOICES
    GHOST_FACE = "en_us_ghostface"
    CHEWBACCA = "en_us_chewbacca"
    C3PO = "en_us_c3po"
    STITCH = "en_us_stitch"
    STORMTROOPER = "en_us_stormtrooper"
    ROCKET = "en_us_rocket"
    MADAME_LEOTA = "en_female_madam_leota"
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
    SONG_POP_LULLABY = "en_female_f08_twinkle"
    SONG_QUIRKY = "en_male_m2_xhxs_m03_silly"
    # OTHER
    STORY_TELLER = "en_male_narration"
    WACKY = "en_male_funny"
    SERIOUS = "en_male_cody"
    EMPATHETIC = "en_female_samc"
    ALFRED = "en_male_jarvis"
    BAE = "en_female_betty"
    BEAUTY_GURU = "en_male_santa_narration"
    SANTA = "en_male_santa"
    SANTA_WO_EFFECT = "en_male_santa_effect"
    BESTIE = "en_female_richgirl"
    CUPID = "en_male_cupid"
    GHOST_HOST = "en_male_ghosthost"
    LORD_CRINGE = "en_male_ukneighbor"
    MAGICIAN = "en_male_wizard"
    MARTY = "en_male_trevor"
    DEBUTANTE = "en_female_shenna"
    AUTHOR = "en_female_makeup"
    PEACEFUL = "en_female_emotional"
    GRANDMA = "en_female_grandma"
    TRICKSTER_GRINCH = "en_male_grinch"
    GOODGUY_DEADPOOL = "en_male_deadpool"
    METICULOUS = "en_male_ukbutler"
    OPTIMUS_PRIME = "en_male_petercullen"
    PIRATE = "en_male_pirate"
    VARSITY = "en_female_pansino"


for voice in Voices:
    assert voice.name == voice.name.upper(), voice.name

CACHE_LIMIT = 1000
generated_tts_cache: OrderedDict[tuple[Voices, str], tuple[str, float]] = OrderedDict()


API_DOMAINS = [
    "https://api16-normal-c-useast2a.tiktokv.com",
    # The following don't seem to be working
    # "https://api16-normal-v6.tiktokv.com",
    # "https://api16-normal-c-useast1a.tiktokv.com",
    # "https://api16-normal-c-useast1a.tiktokv.com",
    # "https://api16-core-c-useast1a.tiktokv.com",
    # "https://api16-normal-useast5.us.tiktokv.com",
    # "https://api16-core.tiktokv.com",
    # "https://api16-core-useast5.us.tiktokv.com",
    # "https://api19-core-c-useast1a.tiktokv.com",
    # "https://api-core.tiktokv.com",
    # "https://api-normal.tiktokv.com",
    # "https://api19-normal-c-useast1a.tiktokv.com",
    # "https://api16-core-c-alisg.tiktokv.com",
    # "https://api16-normal-c-alisg.tiktokv.com",
    # "https://api22-core-c-alisg.tiktokv.com",
]
API_PATH = "/media/api/text/speech/invoke/"


async def generate_tts(voice: Voices, text: str) -> tuple[str, float]:
    key = (voice, text)
    if key in generated_tts_cache:
        # Refresh cache / order - was recently accessed so re-add it
        generated_tts_cache[key] = generated_tts_cache.pop(key)
        return generated_tts_cache[key]

    async with httpx.AsyncClient() as client:
        headers = {
            "User-Agent": "com.zhiliaoapp.musically/2022600030 (Linux; U; Android 7.1.2; es_ES; SM-G988N; Build/NRD90M;tt-ok/3.12.13.1)",  # noqa: E501
            "Cookie": f"sessionid={os.getenv('TIKTOK_SESSION_ID')}",
        }

        data = {}
        status_code = 1
        for domain in API_DOMAINS:
            url = f"{domain}{API_PATH}?text_speaker={voice.value}&req_text={text}&speaker_map_type=0&aid=1233"
            response = await client.post(url, headers=headers)
            if response.is_error:
                continue
            data = response.json()

            status_code: int = data["status_code"]
            # message: str = data["message"]
            # status_msg: str = data["status_msg"]
            if status_code == 0:
                break

        assert status_code == 0, f"{data=}"

        if len(generated_tts_cache) > CACHE_LIMIT:
            # FIFO removal
            generated_tts_cache.popitem(last=False)

        # Calculate the real duration
        b64data = data["data"]["v_str"]
        b64data_decoded = base64.b64decode(b64data)
        data = BytesIO(b64data_decoded)
        mp3_info = MP3(data)
        real_duration_seconds = mp3_info.info.length
        # logger.info(f"Data was off by: {real_duration_seconds - calc_duration}")

        generated_tts_cache[key] = b64data, real_duration_seconds
        return generated_tts_cache[key]


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
