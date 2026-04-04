from __future__ import annotations

import re
from stat import S_IFREG

import arrow
from dataclasses import dataclass
from pydantic import BaseModel
from stream_zip import NO_COMPRESSION_64, async_stream_zip

from minio_helper import (
    GARAGE_AUDIOBOOK_BUCKET,
    get_s3_client,
    object_delete,
    object_download,
    object_upload_async_iterable,
)
from models.audiobook import AudiobookBook, AudiobookChapter
from piccolo_conf import DB


@dataclass
class AudioSettings:
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
        return cls(**data.__dict__)


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


class AudiobookChapterQueryResult(BaseModel):
    id: int
    book_id: int
    number_in_queue: int | None  # 'None' if converting or not queued
    is_converting: bool
    has_audio: bool
    chapter_title: str
    chapter_number: int
    # word_count: int
    sentence_count: int
    minio_object_name: str | None
    # Filled after query
    minio_presigned_url: str = ""


def get_book_minio_zip_name(book_id: int) -> str:
    return f"book_{book_id}.zip"


async def delete_audio_for_chapters(chapters: list[AudiobookChapterQueryResult]) -> None:
    # Delete audiobook zip from minio if exists
    # Delete audio for chapter from minio if exists
    # Set chapters to not have audio for ids
    if len(chapters) == 0:
        return
    chapter_ids: list[int] = [chapter.id for chapter in chapters]
    async with DB.transaction():
        async with get_s3_client() as s3:
            # Delete book zip - doesn't matter as we re-generate the zip for each download
            # await object_delete(s3, AUDIOBOOK_BUCKET, get_book_minio_zip_name(book_id))

            # Delete audio for chapters
            for chapter in chapters:
                if chapter.minio_object_name is None:
                    continue
                await object_delete(s3, GARAGE_AUDIOBOOK_BUCKET, chapter.minio_object_name)

        # Set chapters in db to unqueued
        await AudiobookChapter.update(
            {
                AudiobookChapter.queued: None,
                AudiobookChapter.started_converting: None,
                AudiobookChapter.minio_object_name: None,
                AudiobookChapter.audio_settings: None,
            }
        ).where(
            # pyrefly: ignore
            AudiobookChapter.id.is_in(chapter_ids)
        )


async def upload_multipart_book(book: AudiobookBook, chapters: list[AudiobookChapterQueryResult]):
    assert book is not None
    normalized_author = f"{normalize_title(book.custom_book_author or book.book_author)}"[:50].strip()
    normalized_book_title = f"{normalize_title(book.custom_book_title or book.book_title)}"[:150].strip()

    async with get_s3_client() as s3:

        async def chapter_audio_chunks():
            for chapter in chapters:
                assert chapter.minio_object_name is not None
                obj = await object_download(s3, GARAGE_AUDIOBOOK_BUCKET, chapter.minio_object_name)
                assert obj is not None

                async def yield_data():
                    assert obj is not None
                    yield obj

                normalized_chapter_name = normalize_filename(chapter.chapter_title)[:200].strip()
                audio_file_name = f"{normalized_author}/{normalized_book_title}/{chapter.chapter_number:04d}_{normalized_chapter_name}.mp3"  # noqa: E501
                yield (
                    audio_file_name,
                    arrow.utcnow().naive,
                    S_IFREG | 0o600,
                    # ZIP_64,  # Use compression to save about 4%
                    NO_COMPRESSION_64,  # Don't use compression
                    yield_data(),
                )

        await object_upload_async_iterable(
            s3,
            GARAGE_AUDIOBOOK_BUCKET,
            # pyrefly: ignore
            get_book_minio_zip_name(book.id),
            async_stream_zip(chapter_audio_chunks()),
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


def get_chapter_combined_text(text: str) -> str:
    # Text still contains "\n" characters
    combined = " ".join(row for row in text)
    return re.sub(r"\s+", " ", combined)
