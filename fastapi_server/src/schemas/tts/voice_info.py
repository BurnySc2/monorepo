from __future__ import annotations

from pydantic import BaseModel

from schemas.tts.engine import TTSEngine


class VoiceInfo(BaseModel):
    engine: TTSEngine
    internal_name: str
    label: str
    gender: str | None = None
    locale: str | None = None


__all__ = ["VoiceInfo"]
