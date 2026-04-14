from __future__ import annotations

import re
from stat import S_IFREG

import arrow
from stream_zip import NO_COMPRESSION_64, async_stream_zip

from piccolo_conf import DB
from s3_helper import (
    RUSTFS_AUDIOBOOK_BUCKET,
    get_s3_client,
    object_delete,
    object_download,
    object_upload_async_iterable,
)
from schemas.audiobook.api_models import AudiobookChapterQueryResult
from schemas.audiobook.db_models import AudiobookBook, AudiobookChapter


def get_book_minio_zip_name(book_id: int) -> str:
    return f"book_{book_id}.zip"


async def delete_audio_for_chapters(chapters: list[AudiobookChapterQueryResult]) -> None:
    if len(chapters) == 0:
        return
    chapter_ids: list[int] = [chapter.id for chapter in chapters]
    async with DB.transaction():
        async with get_s3_client() as s3:
            for chapter in chapters:
                if chapter.minio_object_name is None:
                    continue
                await object_delete(s3, RUSTFS_AUDIOBOOK_BUCKET, chapter.minio_object_name)

        await AudiobookChapter.update(
            {
                AudiobookChapter.queued: None,
                AudiobookChapter.started_converting: None,
                AudiobookChapter.minio_object_name: None,
                AudiobookChapter.audio_settings: None,
            }
        ).where(AudiobookChapter.id.is_in(chapter_ids))


async def upload_multipart_book(book: AudiobookBook, chapters: list[AudiobookChapterQueryResult]):
    assert book is not None
    normalized_author = f"{normalize_title(book.custom_book_author or book.book_author)}"[:50].strip()
    normalized_book_title = f"{normalize_title(book.custom_book_title or book.book_title)}"[:150].strip()

    async with get_s3_client() as s3:

        async def chapter_audio_chunks():
            for chapter in chapters:
                assert chapter.minio_object_name is not None
                obj = await object_download(s3, RUSTFS_AUDIOBOOK_BUCKET, chapter.minio_object_name)
                assert obj is not None

                async def yield_data():
                    assert obj is not None
                    yield obj

                normalized_chapter_name = normalize_filename(chapter.chapter_title)[:200].strip()
                audio_file_name = (
                    f"{normalized_author}/{normalized_book_title}/"
                    f"{chapter.chapter_number:04d}_{normalized_chapter_name}.mp3"
                )
                yield (
                    audio_file_name,
                    arrow.utcnow().naive,
                    S_IFREG | 0o600,
                    NO_COMPRESSION_64,
                    yield_data(),
                )

        await object_upload_async_iterable(
            s3,
            RUSTFS_AUDIOBOOK_BUCKET,
            get_book_minio_zip_name(book.id),
            async_stream_zip(chapter_audio_chunks()),
        )


def normalize_title(title: str) -> str:
    normalized_title = title.title()
    normalized_title = re.sub(r"[^\w]", " ", normalized_title)
    normalized_title = re.sub(r" +", " ", normalized_title)
    return normalized_title.strip()


def normalize_filename(text: str) -> str:
    return re.sub(" ", "_", normalize_title(text))


def get_chapter_combined_text(text: str) -> str:
    combined = " ".join(row for row in text)
    return re.sub(r"\s+", " ", combined)
