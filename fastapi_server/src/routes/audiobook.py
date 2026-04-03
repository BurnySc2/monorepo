import io
from pathlib import Path

import arrow
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from components.audiobook.epub_reader import extract_chapters, extract_metadata
from components.audiobook.generate_tts import get_supported_voices
from components.audiobook.models import AudioSettingsBaseModel
from minio_helper import GARAGE_AUDIOBOOK_BUCKET, get_s3_client, object_create_presigned_url, object_delete
from models.audiobook import AudiobookBook, AudiobookChapter

_queries_directory = Path(__file__).parent.parent / "queries"
_query_get_chapters = (_queries_directory / "audiobook_get_chapters.sql").read_text()

audiobook_router = APIRouter()


@audiobook_router.get("/books")
async def list_books() -> JSONResponse:
    """
    List all non-deleted books with chapter counts.
    """
    books = (
        await AudiobookBook.objects()
        .where(AudiobookBook.deleted == False)  # noqa: E712
        .order_by(AudiobookBook.upload_date, ascending=False)
    )

    return JSONResponse(
        [
            {
                "id": book.id,
                "uploaded_by": book.uploaded_by,
                "book_title": book.book_title,
                "book_author": book.book_author,
                "custom_book_title": book.custom_book_title,
                "custom_book_author": book.custom_book_author,
                "chapter_count": book.chapter_count,
                "upload_date": arrow.get(book.upload_date).isoformat(),
            }
            for book in books
        ]
    )


@audiobook_router.get("/books/{book_id}")
async def get_book(book_id: int) -> JSONResponse:
    """
    Get a single book with its chapters.
    Returns 404 if not found.
    Generates presigned URLs for chapters with audio.
    Uses optimized SQL query to get global queue position.
    """
    book = await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()

    if book is None or book.deleted:
        return JSONResponse({"error": "Book not found"}, status_code=404)

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
                        bucket=GARAGE_AUDIOBOOK_BUCKET,
                        key=row["minio_object_name"],
                        file_name=f"{row['chapter_title']}.mp3",
                        expires_in_seconds=3600,
                        verify_object_exists=False,
                    )
                    or ""
                )

            chapters_data.append(
                {
                    "id": row["id"],
                    "book_id": row["book_id"],
                    "number_in_queue": row["number_in_queue"],
                    "is_converting": row["is_converting"],
                    "has_audio": row["has_audio"],
                    "chapter_title": row["chapter_title"],
                    "chapter_number": row["chapter_number"],
                    "sentence_count": row["sentence_count"],
                    "minio_object_name": row["minio_object_name"],
                    "minio_presigned_url": presigned_url,
                }
            )

    available_voices: list[str] = []

    return JSONResponse(
        {
            "book": {
                "id": book.id,
                "uploaded_by": book.uploaded_by,
                "book_title": book.book_title,
                "book_author": book.book_author,
                "custom_book_title": book.custom_book_title,
                "custom_book_author": book.custom_book_author,
                "chapter_count": book.chapter_count,
                "upload_date": arrow.get(book.upload_date).isoformat(),
            },
            "chapters": chapters_data,
            "available_voices": available_voices,
        }
    )


@audiobook_router.post("/upload")
async def upload_epub(file: UploadFile = File(...)) -> JSONResponse:
    """
    Upload an epub file, parse it, and create book/chapter records.
    Returns 400 if not an epub, 201 on success.
    """
    if not file.filename or not file.filename.lower().endswith(".epub"):
        return JSONResponse({"error": "File must be an epub"}, status_code=400)

    try:
        contents = await file.read()
        data = io.BytesIO(contents)

        # Extract metadata and chapters
        metadata = extract_metadata(data)
        chapters = extract_chapters(data)

        # Reset file position for re-reading if needed
        data.seek(0)

        # Create book record
        book = AudiobookBook(
            uploaded_by="system",  # TODO: get from auth
            book_title=metadata.title,
            book_author=metadata.author,
            chapter_count=len(chapters),
            upload_date=arrow.utcnow().naive,
        )
        await book.save()

        # Create chapter records
        for chapter in chapters:
            chapter_record = AudiobookChapter(
                book=book.id,
                chapter_title=chapter.chapter_title,
                chapter_number=chapter.chapter_number,
                word_count=chapter.word_count,
                sentence_count=chapter.sentence_count,
                content=chapter.combined_text,
            )
            await chapter_record.save()

        return JSONResponse({"id": book.id, "title": book.book_title}, status_code=201)

    except OSError as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@audiobook_router.delete("/books/{book_id}")
async def delete_book(book_id: int) -> JSONResponse:
    """
    Soft delete a book and clear queued status on its chapters.
    Returns 404 if not found.
    """
    book = await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()

    if book is None or book.deleted:
        return JSONResponse({"error": "Book not found"}, status_code=404)

    # Soft delete the book
    book.deleted = True
    await book.save()

    # Clear queued status on all chapters
    await AudiobookChapter.update({AudiobookChapter.queued: None}).where(AudiobookChapter.book == book_id)

    return JSONResponse({"deleted": True})


@audiobook_router.get("/voices")
async def list_voices() -> JSONResponse:
    """
    List all available TTS voices.
    """
    voices = await get_supported_voices()
    return JSONResponse(voices)


class QueueChapterRequest(BaseModel):
    voice: str
    rate: int = 0
    volume: int = 0
    pitch: int = 0


@audiobook_router.post("/books/{book_id}/chapters/{chapter_id}/queue")
async def queue_chapter(book_id: int, chapter_id: int, settings: QueueChapterRequest) -> JSONResponse:
    """
    Queue a chapter for audio conversion.
    Sets queued timestamp and stores audio settings.
    """
    book = await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    if book is None or book.deleted:
        return JSONResponse({"error": "Book not found"}, status_code=404)

    chapter = (
        await AudiobookChapter.objects()
        .where(AudiobookChapter.id == chapter_id)
        .where(AudiobookChapter.book == book_id)
        .first()
    )
    if chapter is None:
        return JSONResponse({"error": "Chapter not found"}, status_code=404)

    audio_settings = AudioSettingsBaseModel(
        voice=settings.voice,
        rate=settings.rate,
        volume=settings.volume,
        pitch=settings.pitch,
    )

    chapter.queued = arrow.utcnow().naive
    chapter.audio_settings = audio_settings.model_dump_json()
    await chapter.save()

    return JSONResponse({"queued": True})


@audiobook_router.delete("/books/{book_id}/chapters/{chapter_id}/queue")
async def cancel_queued_chapter(book_id: int, chapter_id: int) -> JSONResponse:
    """
    Cancel a queued chapter conversion.
    Clears the queued timestamp and audio settings.
    """
    book = await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    if book is None or book.deleted:
        return JSONResponse({"error": "Book not found"}, status_code=404)

    chapter = (
        await AudiobookChapter.objects()
        .where(AudiobookChapter.id == chapter_id)
        .where(AudiobookChapter.book == book_id)
        .first()
    )
    if chapter is None:
        return JSONResponse({"error": "Chapter not found"}, status_code=404)

    chapter.queued = None
    chapter.audio_settings = None
    await chapter.save()

    return JSONResponse({"cancelled": True})


@audiobook_router.delete("/books/{book_id}/chapters/{chapter_id}/audio")
async def delete_chapter_audio(book_id: int, chapter_id: int) -> JSONResponse:
    """
    Delete the generated audio for a chapter.
    Removes the audio from Garage and clears the minio_object_name.
    """
    book = await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()
    if book is None or book.deleted:
        return JSONResponse({"error": "Book not found"}, status_code=404)

    chapter = (
        await AudiobookChapter.objects()
        .where(AudiobookChapter.id == chapter_id)
        .where(AudiobookChapter.book == book_id)
        .first()
    )
    if chapter is None:
        return JSONResponse({"error": "Chapter not found"}, status_code=404)

    if chapter.minio_object_name:
        async with get_s3_client() as s3:
            await object_delete(s3, GARAGE_AUDIOBOOK_BUCKET, chapter.minio_object_name)

        chapter.minio_object_name = None
        await chapter.save()

    return JSONResponse({"deleted": True})
