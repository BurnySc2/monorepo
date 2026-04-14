from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AudioSettings(BaseModel):
    engine_name: str = ""
    voice_name: str = ""


class Book(BaseModel):
    id: int
    chapters_count: int
    title: str
    author: str
    custom_title: str = ""
    custom_author: str = ""


class Chapter(BaseModel):
    id: int
    number: int
    title: str
    custom_title: str = ""
    word_count: int
    sentence_count: int
    queued: bool
    queued_position: int
    audio_generated: bool
    audio_url: str


class AudiobookChapterQueryResult(BaseModel):
    id: int
    book_id: int
    number_in_queue: int | None = None
    is_converting: bool
    has_audio: bool
    chapter_title: str
    chapter_number: int
    sentence_count: int
    minio_object_name: str | None = None
    minio_presigned_url: str = ""


class BookListItem(BaseModel):
    id: int
    uploaded_by: str
    book_title: str
    book_author: str
    custom_book_title: str | None = None
    custom_book_author: str | None = None
    chapter_count: int
    upload_date: datetime


class ChapterDetail(BaseModel):
    id: int
    book_id: int
    number_in_queue: int | None = None
    is_converting: bool
    has_audio: bool
    chapter_title: str
    chapter_number: int
    sentence_count: int
    minio_object_name: str | None = None
    minio_presigned_url: str = ""


class BookWithChapters(BaseModel):
    book: BookListItem
    chapters: list[ChapterDetail]
    available_voices: list[str]


class UploadSuccess(BaseModel):
    id: int
    title: str


class DeleteResponse(BaseModel):
    deleted: bool


class QueueResponse(BaseModel):
    queued: bool


class CancelQueueResponse(BaseModel):
    cancelled: bool


class QueueChapterRequest(BaseModel):
    voice: str
    engine: str


__all__ = [
    "AudioSettings",
    "Book",
    "Chapter",
    "AudiobookChapterQueryResult",
    "BookListItem",
    "ChapterDetail",
    "BookWithChapters",
    "UploadSuccess",
    "DeleteResponse",
    "QueueResponse",
    "CancelQueueResponse",
    "QueueChapterRequest",
]
