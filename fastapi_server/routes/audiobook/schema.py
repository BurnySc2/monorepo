from __future__ import annotations

import base64
import datetime
import json
import os
import re
from functools import cached_property
from typing import Any

import dataset  # pyre-fixme[21]
from dotenv import load_dotenv
from minio import Minio
from pydantic import BaseModel, model_validator

load_dotenv()
STAGE = os.getenv("STAGE", "dev")

# pyre-fixme[11]
db: dataset.Database = dataset.connect(os.getenv("POSTGRES_CONNECTION_STRING"))


book_table_name = f"litestar_{STAGE}_audiobook_book"
# pyre-fixme[11]
book_table: dataset.Table = db[book_table_name]
chapter_table_name = f"litestar_{STAGE}_audiobook_chapter"
chapter_table: dataset.Table = db[chapter_table_name]

minio_client = Minio(
    # pyre-fixme[6]
    os.getenv("MINIO_URL"),
    os.getenv("MINIO_ACCESS_TOKEN"),
    os.getenv("MINIO_SECRET_KEY"),
)


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


class AudioSettings(BaseModel):
    voice_name: str = ""
    voice_rate: int = 0
    voice_volume: int = 0
    voice_pitch: int = 0


# Database schema
class Book(BaseModel):
    id: int | None = None
    # Twitch user who uploaded the book
    uploaded_by: str
    book_title: str
    book_author: str
    chapter_count: int
    # data: str | None = None
    upload_date: datetime.datetime
    custom_book_title: str = ""
    custom_book_author: str = ""

    # pyre-fixme[56]
    @model_validator(mode="before")
    @classmethod
    def check_card_number_omitted(cls, data: Any) -> Any:
        return data

    # pyre-fixme[14]
    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        return data

    @classmethod
    def encode_data(cls, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    @classmethod
    def decode_data(cls, data: str) -> bytes:
        return base64.b64decode(data)


class Chapter(BaseModel):
    id: int | None = None
    # Related book to this chapter entry
    book_id: int
    chapter_title: str
    chapter_number: int
    word_count: int
    sentence_count: int
    content: list[str] = []
    minio_object_name: str | None = None
    queued: datetime.datetime | None = None
    # Contains datetime if a worker is running. The datetime is the estimated target time
    converting: datetime.datetime | None = None
    audio_settings: AudioSettings = AudioSettings()

    # pyre-fixme[56]
    @model_validator(mode="before")
    @classmethod
    def convert_data(cls, data: Any) -> Any:
        if "content" in data and isinstance(data["content"], str):
            # From database: this will be a string
            data["content"] = json.loads(data["content"])
        return data

    # pyre-fixme[14]
    def model_dump(self, **kwargs) -> dict[str, Any]:
        """
        Model dump to database entry. id should be created by the database, so it should be excluded when inserting,
        but included when updating.

        Convert 'content' to json string
        Convert audio data from bytes to string
        """
        data = super().model_dump(**kwargs)
        data["content"] = json.dumps(data["content"])
        return data

    @cached_property
    def audio_data(self) -> bytes:
        assert isinstance(self.minio_object_name, str)
        # pyre-fixme[6]
        return minio_client.get_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{self.id}_audio.mp3").data

    @cached_property
    def audio_data_b64(self) -> str:
        assert isinstance(self.audio_data, bytes)
        return Book.encode_data(self.audio_data)

    @cached_property
    def combined_text(self) -> str:
        # Text still contains "\n" characters
        combined = " ".join(row for row in self.content)
        return re.sub(r"\s+", " ", combined)

    @cached_property
    def position_in_queue(self) -> int:
        if not self.queued or self.converting or self.minio_object_name:
            return -1
        return chapter_table.count(queued={"<=": self.queued}, converting=None, minio_object_name=None)
