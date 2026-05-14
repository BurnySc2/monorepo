import base64
from typing import cast

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from components.tts_generate import generate_audio, list_all_voices
from schemas.tts import ENGINES
from schemas.tts.engine import TTSEngine
from schemas.tts.voice_info import VoiceInfo


class TTSGenerateRequest(BaseModel):
    voice: str
    text: str


tts_generate_router = APIRouter()

AUDIOBOOK_ENGINES: list[TTSEngine] = ["tiktok", "edge"]


@tts_generate_router.get("/voices-audiobook", response_model=list[VoiceInfo])
async def list_audiobook_voices() -> list[VoiceInfo]:
    """
    List TTS voices available for audiobook generation.
    Only returns voices from tiktok and edge engines (kokoro/kitten excluded - too slow for server CPU).
    """
    all_voices = await list_all_voices()
    return [v for v in all_voices if v.engine in AUDIOBOOK_ENGINES]


@tts_generate_router.get("/voices", response_model=list[VoiceInfo])
async def list_voices() -> list[VoiceInfo]:
    """
    List all available TTS voices.
    """
    return await list_all_voices()


@tts_generate_router.post("/generate")
async def generate_tts(request: TTSGenerateRequest) -> dict:
    """
    Generate TTS audio for the given voice and text.
    Voice should be in format: {engine}_{voice_name}
    Returns base64-encoded MP3 audio.
    """
    parts = request.voice.split("_", 1)
    if len(parts) != 2:
        raise HTTPException(status_code=400, detail="Invalid voice format")
    engine_str, voice_name = parts

    if engine_str not in ENGINES:
        raise HTTPException(status_code=400, detail=f"Unknown engine: {engine_str}. Supported: {ENGINES}")

    engine = cast(TTSEngine, engine_str)
    audio_bytes, duration = await generate_audio(engine, voice_name, request.text)

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {"audio_b64": audio_b64, "duration": duration}
