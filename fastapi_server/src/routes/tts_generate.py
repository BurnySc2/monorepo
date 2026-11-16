import asyncio
import base64
from contextlib import suppress
from io import BytesIO
from typing import cast

from fastapi import APIRouter, HTTPException
from mutagen import MutagenError
from mutagen.mp3 import MP3
from pydantic import BaseModel, Field

from components.audiobook.epub_reader import ensure_nltk_data
from components.tts_generate import generate_audio, get_voice_by_internal, get_voice_by_label, list_all_voices
from components.tts_generate.tts_sample_cache import (
    MAX_TEXT_LENGTH,
    get_key_lock,
    is_canonical_sample,
    read_cached,
    sample_cache_key,
    write_cached_atomic,
)
from schemas.tts import ENGINES
from schemas.tts.engine import TTSEngine
from schemas.tts.voice_info import VoiceInfo


class TTSGenerateRequest(BaseModel):
    voice: str
    text: str = Field(max_length=MAX_TEXT_LENGTH)


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

    ensure_nltk_data()
    engine = cast(TTSEngine, engine_str)
    await list_all_voices()
    voice_info = get_voice_by_internal(engine_str, voice_name) or get_voice_by_label(engine_str, voice_name)
    resolved_voice = voice_info.internal_name if voice_info is not None else voice_name
    cache_source = voice_info.label if voice_info is not None else voice_name
    if is_canonical_sample(request.text):
        normalized_label = cache_source.lower().replace("_", " ")
        key = sample_cache_key(engine, normalized_label, request.text)
        async with get_key_lock(key):
            cached = await read_cached(key)
            if cached is not None:
                try:
                    audio = await asyncio.to_thread(MP3, BytesIO(cached))
                except MutagenError as exc:
                    raise HTTPException(status_code=502, detail="Invalid cached audio") from exc
                if audio.info is None:
                    raise HTTPException(status_code=502, detail="Invalid cached audio")
                audio_b64 = base64.b64encode(cached).decode("utf-8")
                return {"audio_b64": audio_b64, "duration": audio.info.length}
            try:
                audio_bytes, duration = await generate_audio(engine, resolved_voice, request.text)
            except ValueError as exc:
                raise HTTPException(status_code=400, detail=str(exc)) from exc
            with suppress(Exception):
                await write_cached_atomic(key, audio_bytes)
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
            return {"audio_b64": audio_b64, "duration": duration}

    try:
        audio_bytes, duration = await generate_audio(engine, resolved_voice, request.text)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")
    return {"audio_b64": audio_b64, "duration": duration}
