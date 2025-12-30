from __future__ import annotations

import asyncio
import os
from datetime import timedelta
from pathlib import Path
from stat import S_IFREG
from typing import Annotated

import arrow
from litestar import Controller, Request, Response, get, post
from litestar.contrib.htmx.response import ClientRedirect
from litestar.datastructures import Cookie
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.params import Body
from litestar.response import Stream, Template
from pydantic import BaseModel
from routes.audiobook.my_minio_client import (
    MINIO_AUDIOBOOK_BUCKET,
    AudioSettings,
    hard_delete_book,
    minio_check_if_object_exists,
    minio_client,
    normalize_filename,
    normalize_title,
)
from routes.audiobook.temp_generate_tts import get_supported_voices
from routes.cookies_and_guards import (
    LoggedInUser,
    get_user_settings,
    is_logged_in_guard,
    owns_book_guard,
    provide_logged_in_user,
)
from stream_zip import ZIP_64, async_stream_zip

from models.audiobook import AudiobookBook, AudiobookChapter

queries_directory = Path(__file__).parents[2] / "queries"
query_get_book = (queries_directory / "audiobook_book_metadata.sql").read_text()
query_get_chapters = (queries_directory / "audiobook_get_chapters.sql").read_text()
query_queue_all_chapters = (queries_directory / "audiobook_queue_all.sql").read_text()


class BookContext(BaseModel):
    # Context Model for get_book_by_id
    book_id: int
    book_name: str
    book_author: str
    chapter_count: int
    chapters_for_input_as_string: str
    user_settings: AudioSettings
    available_voices: list[str]
    show_button_generate_all_audio: bool
    show_button_download_book: bool
    show_button_delete_all_audio: bool


class ChapterAudioGenerateContext(BaseModel):
    # Context Model for generate_audio
    pass


class ChapterAudioLoadContext(BaseModel):
    # Context Model for load_generated_audio
    pass


class ChapterAudioDeleteContext(BaseModel):
    # Context Model for delete_generated_audio
    pass


class AudiobookBookMetadataQuery(BaseModel):
    # Context Model for delete_generated_audio
    book_id: int
    book_title: str
    book_author: str
    chapter_count: int
    show_button_generate_all_audio: bool
    show_button_download_book: bool
    show_button_delete_all_audio: bool

    @property
    def chapters_for_input_as_string(self) -> str:
        return ",".join(map(str, range(1, self.chapter_count + 1)))


class AudiobookChapterQuery(BaseModel):
    # Class used in other contexts
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


def update_refresh_queue(
    current_queue: str,
    new_chapters: set[int] | set[str],
) -> str:
    refresh_queue = set(current_queue.split(","))
    refresh_queue.discard("")
    refresh_queue |= {str(i) for i in new_chapters}
    new_refresh_queue = ",".join(refresh_queue)
    return new_refresh_queue


async def minio_presigned_get_object(object_name: str) -> str:
    url = await asyncio.to_thread(
        minio_client.presigned_get_object,
        bucket_name=MINIO_AUDIOBOOK_BUCKET,
        object_name=object_name,
        expires=timedelta(hours=24),
    )
    return url


class MyAudiobookBookRoute(Controller):
    path = "/audiobook"
    guards = [is_logged_in_guard]
    dependencies = {
        "logged_in_user": Provide(provide_logged_in_user),
    }

    @get("/book/{book_id: int}", dependencies={"user_settings": Provide(get_user_settings)}, guards=[owns_book_guard])
    async def get_book_by_id(
        self,
        user_settings: AudioSettings,
        book_id: int,
        logged_in_user: LoggedInUser,
    ) -> Template:
        book_metadata_raw = await AudiobookBook.raw(query_get_book, book_id, book_id, book_id)
        if book_metadata_raw is None:
            # TODO Book does not belong to this person, is deleted or does not exist
            raise IndexError()
        if book_metadata_raw:
            book_metadata = AudiobookBookMetadataQuery(**book_metadata_raw[0])
        available_voices = await get_supported_voices()
        return Template(
            template_name="audiobook/epub_book.html",
            context=BookContext(
                book_id=book_metadata.book_id,
                book_name=book_metadata.book_title.title(),
                book_author=book_metadata.book_author,
                chapter_count=book_metadata.chapter_count,
                chapters_for_input_as_string=book_metadata.chapters_for_input_as_string,
                show_button_generate_all_audio=book_metadata.show_button_generate_all_audio,
                show_button_download_book=book_metadata.show_button_download_book,
                show_button_delete_all_audio=book_metadata.show_button_delete_all_audio,
                user_settings=user_settings,
                available_voices=available_voices,
            ).model_dump(),
        )

    @post(
        "/generate_audio",
        guards=[owns_book_guard],
    )
    async def generate_audio(
        self,
        book_id: int,
        chapter_number: int,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        """
        Implementation of what happens when user clicks "generate audio" button.
        """
        audio_settings = AudioSettings(
            voice_name=data["voice_name"],
            voice_rate=data["voice_rate"],
            voice_pitch=data["voice_pitch"],
            voice_volume=data["voice_volume"],
        )
        chapters_for_input_as_string = update_refresh_queue(data["hidden_refresh_queue"], {chapter_number})

        # Queue the chapter to the database
        chapter = (
            # pyrefly: ignore
            await AudiobookChapter.objects()
            # pyrefly: ignore
            .where((AudiobookChapter.book == book_id) & (AudiobookChapter.chapter_number == chapter_number))
            .first()
        )
        # Check if already queued
        if chapter and chapter.queued is None:
            chapter.audio_settings = audio_settings.model_dump_json()
            chapter.queued = arrow.utcnow().naive
            await chapter.save()
        return Template(
            template_name="audiobook/epub_refresh.html",
            context={
                "book_id": book_id,
                "chapters_for_input_as_string": chapters_for_input_as_string,
                "chapters": [
                    {
                        "chapter_number": chapter_number,
                        # Will be updated on next refresh
                        "number_in_queue": 0,
                    },
                ],
            },
        )

    @post(
        "/refresh_chapters",
        guards=[owns_book_guard],
    )
    async def refresh_chapters(
        self,
        book_id: int,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        """
        An endpoint for the input:text element to poll information
        if the queued audio chapters have finished generating.
        """
        chapters_as_list: list[str] = data["hidden_refresh_queue"].split(",")

        chapters_info_response = await AudiobookChapter.raw(
            query_get_chapters,
            book_id,
            [int(i) for i in chapters_as_list if i != ""],
        )
        chapters_info = [AudiobookChapterQuery(**row) for row in chapters_info_response]
        for chapter in chapters_info:
            if chapter.minio_object_name is not None:
                # TODO Use async gather to request in parallel?
                presigned_url = await minio_presigned_get_object(chapter.minio_object_name)
                chapter.minio_presigned_url = presigned_url

        chapters_for_input_as_string = update_refresh_queue(
            "",
            {c.chapter_number for c in chapters_info if c.number_in_queue is not None or c.is_converting is True},
        )
        return Template(
            template_name="audiobook/epub_refresh.html",
            context={
                "book_id": book_id,
                "chapters_for_input_as_string": chapters_for_input_as_string,
                "chapters": chapters_info,
            },
        )

    @post(
        "generate_audio_for_book",
        guards=[owns_book_guard],
    )
    async def generate_audio_for_book(
        self,
        logged_in_user: LoggedInUser,
        book_id: int,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        """
        Queue all chapters to generate audio that are not currently queued or generated.
        """
        audio_settings = AudioSettings(
            voice_name=data["voice_name"],
            voice_rate=data["voice_rate"],
            voice_pitch=data["voice_pitch"],
            voice_volume=data["voice_volume"],
        )
        query_result = await AudiobookChapter.raw(query_queue_all_chapters, audio_settings.model_dump_json(), book_id)

        chapters_for_input_as_string = update_refresh_queue(
            data["hidden_refresh_queue"],
            {c["chapter_number"] for c in query_result},
        )

        return Template(
            template_name="audiobook/epub_refresh.html",
            context={
                "book_id": book_id,
                "chapters_for_input_as_string": chapters_for_input_as_string,
                "chapters": [
                    {
                        "chapter_number": c["chapter_number"],
                        # Will be updated on next refresh
                        "number_in_queue": 0,
                    }
                    for c in query_result
                ],
            },
        )

    @get(
        "/download_book_zip",
        media_type=MediaType.TEXT,
        guards=[owns_book_guard],
    )
    async def download_book_zip(
        self,
        book_id: int,
        logged_in_user: LoggedInUser,
    ) -> Stream | None:
        """
        If all chapters have generated audio:

        create zip from all chapters, make download available to user
        """
        book = (
            # pyrefly: ignore
            await AudiobookBook.objects()
            # pyrefly: ignore
            .where((AudiobookBook.id == book_id) & (AudiobookBook.uploaded_by == logged_in_user.db_name))
            .first()
        )
        # TODO If book is None

        # Wait for book audio to be generated
        total_count = book.chapter_count
        for _ in range(60):
            # pyrefly: ignore
            done_count: int = await AudiobookChapter.count().where(
                (AudiobookChapter.book == book_id) & (AudiobookChapter.minio_object_name != None)  # noqa: E711
            )
            if done_count >= total_count:
                break
            await asyncio.sleep(5)
        else:
            # No "break" has been encountered, which means the audio has not been successfully generated
            return None

        normalized_author = f"{normalize_title(book.book_author)}"[:50].strip()
        normalized_book_title = f"{normalize_title(book.book_title)}"[:150].strip()

        book = (
            # pyrefly: ignore
            await AudiobookBook.objects()
            # pyrefly: ignore
            .where((AudiobookBook.id == book_id) & (AudiobookBook.uploaded_by == logged_in_user.db_name))
            .first()
        )
        chapters = (
            await AudiobookChapter.objects()
            # pyrefly: ignore
            .where((AudiobookChapter.book == book_id) & (AudiobookChapter.book.uploaded_by == logged_in_user.db_name))
            .order_by(AudiobookChapter.chapter_number)
        )

        # pyrefly: ignore
        def _minio_get_audio_of_chapter_sync(chapter: AudiobookChapter) -> bytes:
            # pyrefly: ignore
            return minio_client.get_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{chapter.id}_audio.mp3").data

        async def minio_get_audio_of_chapter(chapter: AudiobookChapter) -> bytes:
            # Turn the minio API to be non-blocking by running it in a coroutine
            return await asyncio.to_thread(_minio_get_audio_of_chapter_sync, chapter)

        # Zip files via iterator to use the least amount of memory
        # https://stream-zip.docs.trade.gov.uk/
        # https://stream-zip.docs.trade.gov.uk/get-started/
        # https://stream-zip.docs.trade.gov.uk/async-interface/
        async def async_data(chapter: AudiobookChapter):
            yield await minio_get_audio_of_chapter(chapter)

        async def member_files():
            nonlocal normalized_author, normalized_book_title
            modified_at = arrow.utcnow().naive
            mode = S_IFREG | 0o600
            for chapter in chapters:
                normalized_chapter_name = normalize_filename(chapter.chapter_title)[:200].strip()
                audio_file_name = f"{normalized_author}/{normalized_book_title}/{chapter.chapter_number:04d}_{normalized_chapter_name}.mp3"  # noqa: E501
                yield (
                    audio_file_name,
                    modified_at,
                    mode,
                    ZIP_64,
                    async_data(chapter),
                )

        zipped_chunks = async_stream_zip(member_files(), chunk_size=2**20)

        zip_file_name = f"{normalized_author} - {normalized_book_title}.zip"
        return Stream(
            content=zipped_chunks,
            headers={
                # Change file name
                "Content-Disposition": f"attachment; filename={zip_file_name}",  # noqa: E501
                "Content-Type": "application/zip",
                # Preview of file size, not calculateable when generating zip on the fly
                # "Content-Length": f"{len(bytes_data)}",
                # Unsure what these are for
                "Accept-Encoding": "identity",
                "Content-Transfer-Encoding": "Binary",
            },
        )

    @post("/delete_book", guards=[owns_book_guard])
    async def delete_book(
        self,
        request: Request,
        logged_in_user: LoggedInUser,
        book_id: int,
    ) -> ClientRedirect | None:
        """
        Remove book and all chapters from db and .mp3s from minio
        """
        await hard_delete_book(book_id)

        # hx-remove table row if origin path is overview of uploaded books
        # pyrefly: ignore
        if isinstance(request.headers.get("referer"), str) and request.headers.get("referer").endswith("/audiobook"):
            return None
        return ClientRedirect("/audiobook")

    @post("/delete_generated_audio", guards=[owns_book_guard])
    async def delete_generated_audio(
        self,
        book_id: int,
        chapter_number: int,
    ) -> Template:
        """
        Remove generated audio from db and .mp3 from minio
        """
        chapter = (
            # pyrefly: ignore
            await AudiobookChapter.objects()
            # pyrefly: ignore
            .where((AudiobookChapter.book == book_id) & (AudiobookChapter.chapter_number == chapter_number))
            .first()
        )
        # TODO Raise if chapter is None
        if chapter.minio_object_name is not None:
            object_exists = await minio_check_if_object_exists(MINIO_AUDIOBOOK_BUCKET, chapter.minio_object_name)
            if object_exists:
                await asyncio.to_thread(minio_client.remove_object, MINIO_AUDIOBOOK_BUCKET, chapter.minio_object_name)

        # Update chapter to reset values
        chapter.queued = None
        chapter.started_converting = None
        chapter.minio_object_name = None
        chapter.audio_settings = "{}"
        await chapter.save()

        return Template(
            template_name="audiobook/epub_chapter.html",
            context={
                "book_id": book_id,
                "chapter": {
                    "chapter_number": chapter_number,
                },
            },
        )

    @post("/save_settings_to_cookies")
    async def save_settings_to_cookies(
        self,
        data: Annotated[AudioSettings, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response:
        """
        If all chapters have generated audio:

        create zip from all chapters, make download available to user
        """
        return Response(
            content="",
            cookies=[
                Cookie(key="voice_name", value=data.voice_name, path="/", expires=10**10),
                Cookie(key="voice_rate", value=str(data.voice_rate), path="/", expires=10**10),
                Cookie(key="voice_volume", value=str(data.voice_volume), path="/", expires=10**10),
                Cookie(key="voice_pitch", value=str(data.voice_pitch), path="/", expires=10**10),
            ],
        )
