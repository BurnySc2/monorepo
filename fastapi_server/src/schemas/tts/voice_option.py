from __future__ import annotations

from pydantic import BaseModel

from schemas.tts.voice_info import VoiceInfo


class VoiceOption(BaseModel):
    value: str
    label: str
    engine: str
    locale: str
    gender: str

    @classmethod
    def from_voice_info(cls, voice_info: VoiceInfo, engine: str) -> VoiceOption:
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


__all__ = ["VoiceOption", "VoiceInfo"]
