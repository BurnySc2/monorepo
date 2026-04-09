from dataclasses import dataclass


@dataclass
class VoiceInfo:
    """Information about a TTS voice."""

    name: str
    short_name: str | None = None
    gender: str | None = None
    locale: str | None = None
    language: str | None = None
    description: str | None = None
