import rio
from pydantic import BaseModel


class AudioSettings(rio.UserSettings):
    voice: str = ""
    rate: int = 0
    volume: int = 0
    pitch: int = 0


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
