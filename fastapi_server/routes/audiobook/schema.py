from __future__ import annotations

import base64
import datetime
import json
import os
import time
from typing import Any

import dataset
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()
STAGE = os.getenv("STAGE", "dev")

# pyre-fixme[11]
db: dataset.Database = dataset.connect(os.getenv("POSTGRES_CONNECTION_STRING"))
# TODO Use sqlite instead


# pyre-fixme[11]
book_table_name = f"litestar_{STAGE}_audiobook_book"
book_table: dataset.Table = db[book_table_name]
chapter_table_name = f"litestar_{STAGE}_audiobook_chapter"
chapter_table: dataset.Table = db[chapter_table_name]
audio_table_name = f"litestar_{STAGE}_audiobook_audio"
audio_table: dataset.Table = db[chapter_table_name]


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

    @property
    def has_audio(self) -> bool:
        # TODO Check db if all chapters have audio
        return False

    # TODO add instance method for insert to database
    # TODO add classmethod for 'find' from database
    @classmethod
    def from_dict(cls, my_dict: dict[str, Any]) -> Book:
        # if "data" in my_dict:
        #     my_dict["data"] = Book.encode_data(my_dict["data"])
        return cls(**my_dict)

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
    # key "content" contains the text content in this dictionary
    content: dict = {}
    audio_data: str | None = None
    has_audio: bool = False
    queued: datetime.datetime | None = None
    audio_settings: str = "{}"

    # TODO add cached property for audio settings
    # TODO add cached property for text content

    @property
    def combined_text(self) -> str:
        return " ".join(row for paragraph in self.content["content"] for row in paragraph)

    @property
    def page_end(self) -> int:
        return self.page_start + self.page_count

    @classmethod
    def from_dict(cls, my_dict: dict[str, Any]) -> Chapter:
        # if "content" not in my_dict:
        #     my_dict["content"] = {}
        return cls(**my_dict)

    @classmethod
    def get_metadata(cls, book_id: int) -> list[Chapter]:
        data = db.query(
            f"""
SELECT book_id, chapter_title, chapter_number, word_count, sentence_count, has_audio FROM {chapter_table_name}
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
        return [Chapter.from_dict(result) for result in results]

    @classmethod
    def queue_chapter_to_be_generated(
        cls,
        book_id: int,
        chapter_number: int,
        audio_settings: dict[str, str | int],
    ) -> None:
        with db:
            done_count = chapter_table.count(book_id=book_id, chapter_number=chapter_number, queued={"!=": None})
            # Already queued, don't queue again
            if done_count > 0:
                return
            # Queue chapter to be generated
            db.query(
                f"""
    UPDATE {chapter_table_name}
    SET queued=:datetime_now, audio_settings=:audio_settings
    WHERE book_id=:book_id AND chapter_number=:chapter_number
                """,
                {
                    "datetime_now": datetime.datetime.now(datetime.UTC),
                    "book_id": book_id,
                    "chapter_number": chapter_number,
                    "audio_settings": json.dumps(audio_settings),
                },
            )

    @classmethod
    def delete_audio(cls, book_id: int, chapter_number: int) -> None:
        exists_count: int = chapter_table.count(book_id=book_id, chapter_number=chapter_number, has_audio=True)
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
    def wait_for_audio_to_be_generated(cls, book_id: int, chapter_number: int) -> None:
        while 1:
            # Check if chapter has been generated
            done_count: int = chapter_table.count(book_id=book_id, chapter_number=chapter_number, has_audio=True)
            if done_count > 0:
                break
            time.sleep(5)
