from __future__ import annotations

import base64
import datetime
import json
import os
import re
import time
from typing import Any

import dataset  # pyre-fixme[21]
from dotenv import load_dotenv
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


def normalize_title(title: str) -> str:
    normalized_title = title.capitalize()
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
# pyre-fixme[13]
class Book(BaseModel):
    id: int | None = None
    # Twitch user who uploaded the book
    uploaded_by: str
    book_title: str
    book_author: str
    chapter_count: int
    # data: str | None = None
    upload_date: datetime.datetime

    # pyre-fixme[56]
    @model_validator(mode="before")
    @classmethod
    def check_card_number_omitted(cls, data: Any) -> Any:
        return data

    # pyre-fixme[14]
    def model_dump(self, **kwargs) -> dict[str, Any]:
        data = super().model_dump(**kwargs)
        return data

    @property
    def has_audio(self) -> bool:
        # Check db if all chapters have audio
        return chapter_table.count(book_id=self.id) == self.chapter_count

    @classmethod
    def encode_data(cls, data: bytes) -> str:
        return base64.b64encode(data).decode("utf-8")

    @classmethod
    def decode_data(cls, data: str) -> bytes:
        return base64.b64decode(data)


# pyre-fixme[13]
class Chapter(BaseModel):
    id: int | None = None
    # Related book to this chapter entry
    book_id: int
    chapter_title: str
    chapter_number: int
    word_count: int
    sentence_count: int
    content: list[list[str]] = []
    audio_data: bytes | None = None
    has_audio: bool = False
    queued: datetime.datetime | None = None
    audio_settings: AudioSettings = AudioSettings()

    # pyre-fixme[56]
    @model_validator(mode="before")
    @classmethod
    def convert_data(cls, data: Any) -> Any:
        if "audio_data" in data and data["audio_data"] is not None:
            # From database: this will be a string
            data["audio_data"] = Book.decode_data(data["audio_data"])
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
        if data["audio_data"] is not None:
            # To database: needs to store a string instead of bytes
            data["audio_data"] = Book.encode_data(data["audio_data"])
        return data

    @property
    def audio_data_b64(self) -> str:
        assert isinstance(self.audio_data, bytes)
        return Book.encode_data(self.audio_data)

    @property
    def combined_text(self) -> str:
        # Text still contains "\n" characters
        return " ".join(row for paragraph in self.content for row in paragraph)

    @classmethod
    def get_metadata(cls, book_id: int) -> list[Chapter]:
        data = db.query(
            f"""
SELECT book_id, chapter_title, chapter_number, word_count, sentence_count, has_audio, queued FROM {chapter_table_name}
WHERE book_id=:id
ORDER BY chapter_number
            """,
            {
                "id": book_id,
            },
        )
        results = list(data)
        if len(results) == 0:
            return []
        return [Chapter.model_validate(result) for result in results]

    @classmethod
    def get_chapter_without_audio_data(cls, book_id: int, chapter_number: int) -> Chapter | None:
        data = db.query(
            f"""
SELECT book_id, chapter_title, chapter_number, word_count, sentence_count, has_audio, queued FROM {chapter_table_name}
WHERE book_id=:book_id AND chapter_number=:chapter_number
LIMIT 1
            """,
            {
                "book_id": book_id,
                "chapter_number": chapter_number,
            },
        )
        results = list(data)
        if len(results) == 0:
            return None
        return Chapter.model_validate(results[0])

    @classmethod
    def queue_chapter_to_be_generated(
        cls,
        book_id: int,
        audio_settings: AudioSettings,
        chapter_number: int | None = None,
    ) -> None:
        with db:
            # Queue whole book to be generated
            if chapter_number is None:
                db.query(
                    f"""
        UPDATE {chapter_table_name}
        SET queued=:datetime_now, audio_settings=:audio_settings
        WHERE book_id=:book_id AND queued IS NULL
                    """,
                    {
                        "datetime_now": datetime.datetime.now(datetime.timezone.utc),
                        "audio_settings": audio_settings.model_dump_json(),
                        "book_id": book_id,
                    },
                )
                return

            # Queue chapter to be generated
            db.query(
                f"""
    UPDATE {chapter_table_name}
    SET queued=:datetime_now, audio_settings=:audio_settings
    WHERE book_id=:book_id AND chapter_number=:chapter_number AND queued IS NULL
                """,
                {
                    "datetime_now": datetime.datetime.now(datetime.timezone.utc),
                    "audio_settings": audio_settings.model_dump_json(),
                    "book_id": book_id,
                    "chapter_number": chapter_number,
                },
            )
            1

    @classmethod
    def delete_audio(cls, book_id: int, chapter_number: int) -> None:
        exists_count: int = chapter_table.count(book_id=book_id, chapter_number=chapter_number)
        if exists_count > 0:
            db.query(
                f"""
UPDATE {chapter_table_name}
SET has_audio=False, audio_data=NULL, queued=NULL, audio_settings=:audio_settings
WHERE book_id=:book_id AND chapter_number=:chapter_number
""",
                {
                    "book_id": book_id,
                    "chapter_number": chapter_number,
                    "audio_settings": "{}",
                },
            )

    @classmethod
    def wait_for_audio_to_be_generated(cls, book_id: int, chapter_number: int | None = None) -> None:
        """
        If chapter number is given: Wait for the chapter to be generated.
        Otherwise: Wait for all chapters of the book to be generated.
        """
        total_count: int = 1
        if chapter_number is None:
            total_count = chapter_table.count(book_id=book_id)
        while 1:
            if chapter_number is None:
                # Check if all chapters has been generated
                done_count: int = chapter_table.count(book_id=book_id, has_audio=True)
            else:
                # Check if chapter has been generated
                done_count: int = chapter_table.count(book_id=book_id, chapter_number=chapter_number, has_audio=True)

            if done_count >= total_count:
                return
            time.sleep(5)
