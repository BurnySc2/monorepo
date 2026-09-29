from __future__ import annotations

import io
from typing import Annotated

import arrow
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile

from components.audiobook.epub_reader import extract_chapters, extract_metadata
from components.login.cookies import LoggedInUser, get_current_user
from piccolo_conf import DB
from routes._audiobook_helpers import (
    AUDIO_CLEAR_FIELDS,
    book_to_list_item,
    get_chapters_with_urls,
    get_owned_book,
    parse_chapter_numbers,
)
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

    return [book_to_list_item(book) for book in books]


@audiobook_router.get("/books/{book_id}", response_model=BookWithChapters)
async def get_book(book_id: int, current_user: Annotated[LoggedInUser, Depends(get_current_user)]) -> BookWithChapters:
    """
    Get a single book with its chapters.
    Returns 404 if not found.
    Generates presigned URLs for chapters with audio.
    Uses optimized SQL query to get global queue position.
    """
    book = await get_owned_book(book_id, current_user)

    chapter_numbers = list(range(1, book.chapter_count + 1))
    chapters_data = await get_chapters_with_urls(book_id, chapter_numbers)

    return BookWithChapters(
        book=book_to_list_item(book),
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
    await get_owned_book(book_id, current_user)

    chapter_num_list = parse_chapter_numbers(chapter_numbers)

    return await get_chapters_with_urls(book_id, chapter_num_list)


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


@audiobook_router.delete("/books", response_model=DeleteResponse)
async def delete_all_books(current_user: Annotated[LoggedInUser, Depends(get_current_user)]) -> DeleteResponse:
    """Delete all books of the logged-in user (scoped by uploaded_by).
    Idempotent — returns deleted:true even if no books exist.
    DB-only; S3 objects not deleted (auto-expire after 30 days).
    Relies on FK ON DELETE CASCADE to remove chapters.
    """
    await AudiobookBook.delete().where(
        AudiobookBook.uploaded_by == current_user.db_name  # pyrefly: ignore[missing-attribute]
    )
    return DeleteResponse(deleted=True)


@audiobook_router.delete("/books/{book_id}", response_model=DeleteResponse)
async def delete_book(book_id: int, current_user: Annotated[LoggedInUser, Depends(get_current_user)]) -> DeleteResponse:
    """
    Hard delete a book and all its chapters.
    DB-only; S3 objects not deleted (auto-expire after 30 days).
    Relies on FK ON DELETE CASCADE to remove chapters.
    Returns 404 if not found, 403 if not owned.
    """
    await get_owned_book(book_id, current_user, forbidden_detail="Not authorized to modify this book")

    await AudiobookBook.delete().where(AudiobookBook.id == book_id)  # pyrefly: ignore[missing-attribute]

    return DeleteResponse(deleted=True)


@audiobook_router.delete("/books/{book_id}/audio", response_model=DeleteResponse)
async def delete_all_audio(
    book_id: int,
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> DeleteResponse:
    """
    Delete all generated audio for a book.
    DB-only; clears audio fields via single bulk UPDATE, no S3 deletion (auto-expire).
    Returns 404 if book not found, 403 if not owned.
    """
    await get_owned_book(book_id, current_user)

    await AudiobookChapter.update(AUDIO_CLEAR_FIELDS).where(
        AudiobookChapter.book == book_id  # pyrefly: ignore[missing-attribute]
    )

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
    await get_owned_book(book_id, current_user)

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
    DB-only; clears audio fields via single UPDATE, no S3 deletion (auto-expire).
    Returns 404 if book/chapter not found, 403 if not owned.
    """
    await get_owned_book(book_id, current_user)

    chapter = (
        await AudiobookChapter.objects()
        .where(AudiobookChapter.chapter_number == chapter_id)  # pyrefly: ignore[missing-attribute]
        .where(AudiobookChapter.book == book_id)  # pyrefly: ignore[missing-attribute]
        .first()
    )
    if chapter is None:
        raise HTTPException(status_code=404, detail="Chapter not found")

    await AudiobookChapter.update(AUDIO_CLEAR_FIELDS).where(
        AudiobookChapter.id == chapter.id  # pyrefly: ignore[missing-attribute]
    )

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
    book = await get_owned_book(book_id, current_user)

    book.custom_book_title = body["title"]
    await book.save()

    return book_to_list_item(book)


@audiobook_router.put("/books/{book_id}/author", response_model=BookListItem)
async def update_book_author(
    book_id: int,
    body: Annotated[dict, Body()],
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> BookListItem:
    """
    Update the custom author for a book.
    """
    book = await get_owned_book(book_id, current_user)

    book.custom_book_author = body["author"]
    await book.save()

    return book_to_list_item(book)


@audiobook_router.post("/books/{book_id}/queue-all", status_code=201)
async def queue_all_chapters(
    book_id: int,
    settings: QueueChapterRequest,
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> QueueResponse:
    """
    Queue all chapters of a book for audio conversion.
    """
    await get_owned_book(book_id, current_user)

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
