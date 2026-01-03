from __future__ import annotations

import re

import rio
from pydantic import BaseModel


class AudioSettings(rio.UserSettings):
    voice: str = ""
    rate: int = 0
    volume: int = 0
    pitch: int = 0


class AudioSettingsBaseModel(BaseModel):
    voice: str
    rate: int
    volume: int
    pitch: int

    @classmethod
    def from_dataclass(cls, data: AudioSettings) -> AudioSettingsBaseModel:
        return AudioSettingsBaseModel(**data.__dict__)


class Book(BaseModel):
    # TODO Upload date
    id: int
    chapters_count: int
    title: str
    author: str
    custom_title: str = ""
    custom_autho: str = ""


class Chapter(BaseModel):
    id: int  # id in db
    number: int  # Chapter number in book
    title: str
    custom_title: str = ""
    word_count: int
    sentence_count: int
    queued: bool
    queued_position: int  # <= 0 for generating
    audio_generated: bool
    audio_url: str


def normalize_title(title: str) -> str:
    normalized_title = title.title()
    # Replace any character that is not alphanumeric or underscore with a space
    normalized_title = re.sub(r"[^\w]", " ", normalized_title)
    # Replace two or more space with one space
    normalized_title = re.sub(r" +", " ", normalized_title)
    # Remove space from the start and end
    return normalized_title.strip()


def normalize_filename(text: str) -> str:
    return re.sub(" ", "_", normalize_title(text))


def get_chapter_combined_text(text: str) -> str:
    # Text still contains "\n" characters
    combined = " ".join(row for row in text)
    return re.sub(r"\s+", " ", combined)
