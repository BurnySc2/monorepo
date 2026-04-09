from __future__ import annotations

from pydantic import BaseModel


class VoiceInfo(BaseModel):
    name: str
    short_name: str | None = None
    gender: str | None = None
    locale: str | None = None
    language: str | None = None
    description: str | None = None


__all__ = ["VoiceInfo"]
