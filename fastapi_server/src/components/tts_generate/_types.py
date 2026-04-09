"""
Voice types for TTS generation.
"""

from __future__ import annotations

from pydantic import BaseModel

from components.tts_generate._voice_info import VoiceInfo


class VoiceOption(BaseModel):
    """Voice option for frontend select."""

    value: str
    label: str
    engine: str
    locale: str
    gender: str

    @classmethod
    def from_voice_info(cls, voice_info: VoiceInfo, engine: str) -> VoiceOption:
        """Create VoiceOption from VoiceInfo."""
        locale = voice_info.locale or "unknown"
        gender = voice_info.gender or "unknown"
        short_name = voice_info.short_name or voice_info.name
        voice_name = short_name.replace(" ", "_")

        value = f"{locale}|{engine}|{voice_name}|{gender}"
        label = f"{locale} {engine} {short_name} ({gender})"

        return cls(
            value=value,
            label=label,
            engine=engine,
            locale=locale,
            gender=gender,
        )
