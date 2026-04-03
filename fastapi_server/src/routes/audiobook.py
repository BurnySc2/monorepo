import io

import arrow
from fastapi import APIRouter, File, UploadFile
from fastapi.responses import JSONResponse

from components.audiobook.epub_reader import extract_chapters, extract_metadata
from minio_helper import MINIO_AUDIOBOOK_BUCKET, get_s3_client, object_create_presigned_url
from models.audiobook import AudiobookBook, AudiobookChapter

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
    """
    book = await AudiobookBook.objects().where(AudiobookBook.id == book_id).first()

    if book is None or book.deleted:
        return JSONResponse({"error": "Book not found"}, status_code=404)

    chapters = (
        await AudiobookChapter.objects()
        .where(AudiobookChapter.book == book_id)
        .order_by(AudiobookChapter.chapter_number)
    )

    chapters_data = []
    async with get_s3_client() as s3:
        for chapter in chapters:
            # Generate presigned URL if audio exists
            presigned_url = ""
            if chapter.minio_object_name:
                presigned_url = (
                    await object_create_presigned_url(
                        session=s3,
                        bucket=MINIO_AUDIOBOOK_BUCKET,
                        key=chapter.minio_object_name,
                        file_name=f"{chapter.chapter_title}.mp3",
                        expires_in_seconds=3600,
                        verify_object_exists=False,
                    )
                    or ""
                )

            chapters_data.append(
                {
                    "id": chapter.id,
                    "book_id": chapter.book,
                    "number_in_queue": int(arrow.get(chapter.queued).float_timestamp()) if chapter.queued else None,
                    "is_converting": chapter.started_converting is not None,
                    "has_audio": chapter.minio_object_name is not None,
                    "chapter_title": chapter.chapter_title,
                    "chapter_number": chapter.chapter_number,
                    "sentence_count": chapter.sentence_count,
                    "minio_object_name": chapter.minio_object_name,
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
