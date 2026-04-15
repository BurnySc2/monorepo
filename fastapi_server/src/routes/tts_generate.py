import base64
from typing import cast

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel

from components.tts_generate import generate_audio, list_all_voices
from schemas.tts import ENGINES, VoiceOption
from schemas.tts.engine import TTSEngine


class TTSGenerateRequest(BaseModel):
    voice: str
    text: str


tts_generate_router = APIRouter()


@tts_generate_router.get("/voices", response_model=list[VoiceOption])
async def list_voices() -> list[VoiceOption]:
    """
    List all available TTS voices.
    """
    voices = await list_all_voices()
    return voices


@tts_generate_router.post("/generate")
async def generate_tts(request: TTSGenerateRequest) -> dict:
    """
    Generate TTS audio for the given voice and text.
    Voice should be in format: {locale}|{engine}|{voice_name}|{gender}
    Returns base64-encoded MP3 audio.
    """
    parts = request.voice.split("|")
    if len(parts) != 4:
        raise HTTPException(status_code=400, detail="Invalid voice format")
    logger.info(parts)
    _, engine_str, voice_name, _ = parts

    if engine_str not in ENGINES:
        raise HTTPException(status_code=400, detail=f"Unknown engine: {engine_str}. Supported: {ENGINES}")

    engine = cast(TTSEngine, engine_str)
    audio_bytes, duration = await generate_audio(engine, voice_name, request.text)

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {"audio_b64": audio_b64, "duration": duration}
