from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import HTTPException

from components.login.cookies import LoggedInUser, check_book_ownership
from s3_helper import get_s3_client, object_create_presigned_url
from schemas.audiobook import BookListItem, ChapterDetail
from schemas.audiobook.db_models import AudiobookBook, AudiobookChapter
from settings import settings

_queries_directory = Path(__file__).parent.parent / "queries"
_query_get_chapters = (_queries_directory / "audiobook_get_chapters.sql").read_text()

AUDIO_CLEAR_FIELDS: dict[Any, Any] = {
    AudiobookChapter.minio_object_name: None,
    AudiobookChapter.queued: None,
    AudiobookChapter.started_converting: None,
    AudiobookChapter.audio_settings: None,  # pyrefly: ignore[bad-argument-type,missing-attribute]
}


def parse_chapter_numbers(raw: str | None) -> list[int]:
    """Parse comma-separated chapter numbers into a list of ints.

    Raises 400 if the query param is missing or contains non-integers.
    """
    if raw is None:
        raise HTTPException(status_code=400, detail="chapter_numbers query param required")
    try:
        return [int(x.strip()) for x in raw.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="chapter_numbers must be comma-separated integers") from None


def book_to_list_item(book: AudiobookBook) -> BookListItem:
    """Convert an AudiobookBook row to its API list-item representation."""
    return BookListItem(
        id=book.id,  # pyrefly: ignore[missing-attribute]
        uploaded_by=book.uploaded_by,
        book_title=book.book_title,
        book_author=book.book_author,
        custom_book_title=book.custom_book_title,
        custom_book_author=book.custom_book_author,
        chapter_count=book.chapter_count,
        upload_date=book.upload_date,
    )


async def get_owned_book(
    book_id: int,
    user: LoggedInUser,
    forbidden_detail: str = "Not authorized to access this book",
) -> AudiobookBook:
    """Fetch a book by id, raising 404 if missing and 403 if not owned by user."""
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")
    if not await check_book_ownership(book, user):
        raise HTTPException(status_code=403, detail=forbidden_detail)
    return book


async def get_chapters_with_urls(book_id: int, chapter_numbers: list[int]) -> list[ChapterDetail]:
    """Fetch chapter rows via single SQL query and attach S3 presigned URLs."""
    chapters_rows: list[dict] = await AudiobookChapter.raw(_query_get_chapters, book_id, chapter_numbers)
    chapters_data: list[ChapterDetail] = []
    async with get_s3_client() as s3:
        for row in chapters_rows:
            presigned_url = ""
            if row["minio_object_name"]:
                presigned_url = (
                    await object_create_presigned_url(
                        session=s3,
                        bucket=settings.rustfs_audiobook_bucket,
                        key=row["minio_object_name"],
                        file_name=f"{row['chapter_title']}.mp3",
                        expires_in_seconds=3600,
                        verify_object_exists=False,
                    )
                    or ""
                )
            chapters_data.append(
                ChapterDetail(
                    id=row["id"],
                    book_id=row["book_id"],
                    number_in_queue=row["number_in_queue"],
                    is_converting=row["is_converting"],
                    has_audio=row["has_audio"],
                    chapter_title=row["chapter_title"],
                    chapter_number=row["chapter_number"],
                    sentence_count=row["sentence_count"],
                    minio_object_name=row["minio_object_name"],
                    minio_presigned_url=presigned_url,
                )
            )
    return chapters_data


__all__ = [
    "AUDIO_CLEAR_FIELDS",
    "book_to_list_item",
    "get_chapters_with_urls",
    "get_owned_book",
    "parse_chapter_numbers",
]
