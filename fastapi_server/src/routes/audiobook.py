from __future__ import annotations

import io
from pathlib import Path
from typing import Annotated

import arrow
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile

from components.audiobook.epub_reader import extract_chapters, extract_metadata
from components.login.cookies import LoggedInUser, check_book_ownership, get_current_user
from piccolo_conf import DB
from s3_helper import RUSTFS_AUDIOBOOK_BUCKET, get_s3_client, object_create_presigned_url, object_delete
from schemas.audiobook import (
    AudioSettings,
    BookListItem,
    BookWithChapters,
    ChapterDetail,
    DeleteResponse,
    QueueChapterRequest,
    QueueResponse,
    UploadSuccess,
)
from schemas.audiobook.db_models import AudiobookBook, AudiobookChapter

_queries_directory = Path(__file__).parent.parent / "queries"
_query_get_chapters = (_queries_directory / "audiobook_get_chapters.sql").read_text()

audiobook_router = APIRouter()

ALLOWED_AUDIOBOOK_ENGINES = {"tiktok", "edge"}


def validate_audiobook_engine(settings: QueueChapterRequest) -> None:
    """Validate that engine is allowed for audiobook generation."""
    audio_settings = AudioSettings.from_value(settings.value)
    if audio_settings.engine_name and audio_settings.engine_name not in ALLOWED_AUDIOBOOK_ENGINES:
        raise HTTPException(
            status_code=400,
            detail=f"Engine '{audio_settings.engine_name}' not allowed for audiobook. Use tiktok or edge only.",
        )


@audiobook_router.get("/books", response_model=list[BookListItem])
async def list_books(current_user: Annotated[LoggedInUser, Depends(get_current_user)]) -> list[BookListItem]:
    """
    List all non-deleted books with chapter counts.
    """
    books = (
        await AudiobookBook.objects()
        .where(AudiobookBook.uploaded_by == current_user.db_name)  # noqa: E712
        .order_by(AudiobookBook.upload_date, ascending=False)
    )

    return [
        BookListItem(
            id=book.id,  # pyrefly: ignore[missing-attribute]
            uploaded_by=book.uploaded_by,
            book_title=book.book_title,
            book_author=book.book_author,
            custom_book_title=book.custom_book_title,
            custom_book_author=book.custom_book_author,
            chapter_count=book.chapter_count,
            upload_date=book.upload_date,
        )
        for book in books
    ]


@audiobook_router.get("/books/{book_id}", response_model=BookWithChapters)
async def get_book(book_id: int, current_user: Annotated[LoggedInUser, Depends(get_current_user)]) -> BookWithChapters:
    """
    Get a single book with its chapters.
    Returns 404 if not found.
    Generates presigned URLs for chapters with audio.
    Uses optimized SQL query to get global queue position.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    chapter_numbers = list(range(1, book.chapter_count + 1))
    chapters_rows: list[dict] = await AudiobookChapter.raw(_query_get_chapters, book_id, chapter_numbers)

    chapters_data = []
    async with get_s3_client() as s3:
        for row in chapters_rows:
            presigned_url = ""
            if row["minio_object_name"]:
                presigned_url = (
                    await object_create_presigned_url(
                        session=s3,
                        bucket=RUSTFS_AUDIOBOOK_BUCKET,
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

    return BookWithChapters(
        book=BookListItem(
            id=book.id,  # pyrefly: ignore[missing-attribute]
            uploaded_by=book.uploaded_by,
            book_title=book.book_title,
            book_author=book.book_author,
            custom_book_title=book.custom_book_title,
            custom_book_author=book.custom_book_author,
            chapter_count=book.chapter_count,
            upload_date=book.upload_date,
        ),
        chapters=chapters_data,
        available_voices=[],
    )


@audiobook_router.get("/books/{book_id}/chapters/status", response_model=list[ChapterDetail])
async def get_chapter_status(
    book_id: int,
    chapter_numbers: Annotated[str, ...],
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> list[ChapterDetail]:
    """
    Get status for specific chapters without full book data.
    Accepts comma-separated chapter numbers via query param 'chapter_numbers'.
    Returns only the status fields (queue position, converting, has_audio).
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    if chapter_numbers is None:
        raise HTTPException(status_code=400, detail="chapter_numbers query param required")

    try:
        chapter_num_list = [int(x.strip()) for x in chapter_numbers.split(",")]
    except ValueError:
        raise HTTPException(status_code=400, detail="chapter_numbers must be comma-separated integers")

    chapters_rows: list[dict] = await AudiobookChapter.raw(_query_get_chapters, book_id, chapter_num_list)

    chapters_data = []
    async with get_s3_client() as s3:
        for row in chapters_rows:
            presigned_url = ""
            if row["minio_object_name"]:
                presigned_url = (
                    await object_create_presigned_url(
                        session=s3,
                        bucket=RUSTFS_AUDIOBOOK_BUCKET,
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


@audiobook_router.post("/upload", response_model=UploadSuccess, status_code=201)
async def upload_epub(
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
    file: UploadFile = File(...),
) -> UploadSuccess:
    """
    Upload an epub file, parse it, and create book/chapter records.
    Returns 400 if not an epub, 400 if duplicate, 201 on success.
    """
    if not file.filename or not file.filename.lower().endswith(".epub"):
        raise HTTPException(status_code=400, detail="File must be an epub")

    contents = await file.read()
    data = io.BytesIO(contents)

    metadata = extract_metadata(data)
    chapters = extract_chapters(data)

    # Check for duplicate book
    existing_book = (
        await AudiobookBook.objects()
        .where(
            (AudiobookBook.uploaded_by == current_user.db_name)
            & (AudiobookBook.book_title == metadata.title)
            & (AudiobookBook.book_author == metadata.author)
            & (AudiobookBook.deleted == False)  # noqa: E712
        )
        .first()
    )
    if existing_book:
        raise HTTPException(status_code=409, detail=f"Book '{metadata.title}' by '{metadata.author}' already uploaded")

    async with DB.transaction():
        book = AudiobookBook(
            uploaded_by=current_user.db_name,
            book_title=metadata.title,
            book_author=metadata.author,
            chapter_count=len(chapters),
            upload_date=arrow.utcnow().naive,
        )
        await book.save()

        for chapter in chapters:
            chapter_record = AudiobookChapter(
                book=book.id,  # pyrefly: ignore[missing-attribute]
                chapter_title=chapter.chapter_title,
                chapter_number=chapter.chapter_number,
                word_count=chapter.word_count,
                sentence_count=chapter.sentence_count,
                content=chapter.combined_text,
            )
            await chapter_record.save()

    return UploadSuccess(id=book.id, title=book.book_title)  # pyrefly: ignore[missing-attribute]


@audiobook_router.delete("/books/{book_id}", response_model=DeleteResponse)
async def delete_book(book_id: int, current_user: Annotated[LoggedInUser, Depends(get_current_user)]) -> DeleteResponse:
    """
    Hard delete a book and all its chapters.
    Also deletes S3 audio files for each chapter.
    Returns 404 if not found.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )

    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to modify this book")

    chapters = (
        await AudiobookChapter.objects().where(AudiobookChapter.book == book_id)  # pyrefly: ignore[missing-attribute]
    )

    async with get_s3_client() as s3:
        for chapter in chapters:
            if chapter.minio_object_name:
                await object_delete(s3, RUSTFS_AUDIOBOOK_BUCKET, chapter.minio_object_name)

    async with DB.transaction():
        await AudiobookChapter.delete().where(AudiobookChapter.book == book_id)
        await AudiobookBook.delete().where(AudiobookBook.id == book_id)  # pyrefly: ignore[missing-attribute]

    return DeleteResponse(deleted=True)


@audiobook_router.delete("/books/{book_id}/audio", response_model=DeleteResponse)
async def delete_all_audio(
    book_id: int,
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> DeleteResponse:
    """
    Delete all generated audio for a book.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    chapters = (
        await AudiobookChapter.objects().where(AudiobookChapter.book == book_id)  # pyrefly: ignore[missing-attribute]
    )

    async with get_s3_client() as s3:
        for chapter in chapters:
            if chapter.minio_object_name:
                await object_delete(s3, RUSTFS_AUDIOBOOK_BUCKET, chapter.minio_object_name)
            chapter.minio_object_name = None
            chapter.queued = None
            chapter.started_converting = None
            chapter.audio_settings = None  # pyrefly: ignore[bad-argument-type,missing-attribute]
            await chapter.save()

    return DeleteResponse(deleted=True)


@audiobook_router.post("/books/{book_id}/chapters/{chapter_id}/queue", response_model=QueueResponse)
async def queue_chapter(
    book_id: int,
    chapter_id: int,
    settings: QueueChapterRequest,
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> QueueResponse:
    """
    Queue a chapter for audio conversion.
    Sets queued timestamp and stores audio settings.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    chapter = (
        await AudiobookChapter.objects()
        .where(AudiobookChapter.chapter_number == chapter_id)  # pyrefly: ignore[missing-attribute]
        .where(AudiobookChapter.book == book_id)
        .first()
    )
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")

    validate_audiobook_engine(settings)
    audio_settings = AudioSettings.from_value(settings.value)

    chapter.queued = arrow.utcnow().naive
    chapter.audio_settings = audio_settings.model_dump_json()
    await chapter.save()

    return QueueResponse(queued=True)


@audiobook_router.delete("/books/{book_id}/chapters/{chapter_id}", response_model=DeleteResponse)
async def delete_chapter_audio(
    book_id: int,
    chapter_id: int,
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> DeleteResponse:
    """
    Delete the generated audio for a chapter.
    Removes the audio from rustfs and clears the queued/audio fields.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    chapter = (
        await AudiobookChapter.objects()
        .where(AudiobookChapter.chapter_number == chapter_id)  # pyrefly: ignore[missing-attribute]
        .where(AudiobookChapter.book == book_id)
        .first()
    )
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")

    if chapter.minio_object_name:
        async with get_s3_client() as s3:
            await object_delete(s3, RUSTFS_AUDIOBOOK_BUCKET, chapter.minio_object_name)

    chapter.minio_object_name = None
    chapter.queued = None
    chapter.started_converting = None
    chapter.audio_settings = None  # pyrefly: ignore[bad-argument-type,missing-attribute]
    await chapter.save()

    return DeleteResponse(deleted=True)


@audiobook_router.put("/books/{book_id}/title", response_model=BookListItem)
async def update_book_title(
    book_id: int,
    body: Annotated[dict, Body()],
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> BookListItem:
    """
    Update the custom title for a book.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    book.custom_book_title = body["title"]
    await book.save()

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


@audiobook_router.put("/books/{book_id}/author", response_model=BookListItem)
async def update_book_author(
    book_id: int,
    body: Annotated[dict, Body()],
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> BookListItem:
    """
    Update the custom author for a book.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    book.custom_book_author = body["author"]
    await book.save()

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


@audiobook_router.post("/books/{book_id}/queue-all", status_code=201)
async def queue_all_chapters(
    book_id: int,
    settings: QueueChapterRequest,
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> QueueResponse:
    """
    Queue all chapters of a book for audio conversion.
    """
    book = (
        # pyrefly: ignore[missing-attribute]
        await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    )
    if book is None:
        raise HTTPException(status_code=404, detail="Book not found")

    if not await check_book_ownership(book, current_user):
        raise HTTPException(status_code=403, detail="Not authorized to access this book")

    validate_audiobook_engine(settings)

    await (
        AudiobookChapter.update(
            {
                AudiobookChapter.audio_settings: AudioSettings.from_value(settings.value).model_dump_json(),
                AudiobookChapter.queued: arrow.utcnow().naive,
            }
        )
        # pyrefly: ignore[missing-attribute]
        .where(AudiobookChapter.book == book_id)
        .where(AudiobookChapter.queued.is_null())
    )

    return QueueResponse(queued=True)
