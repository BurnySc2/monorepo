from __future__ import annotations

import datetime
import os
import time
from collections import OrderedDict
from stat import S_IFREG
from typing import Annotated

from litestar import Controller, Response, get, post
from litestar.contrib.htmx.response import ClientRedirect, ClientRefresh
from litestar.datastructures import Cookie
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.params import Body
from litestar.response import Stream, Template
from stream_zip import ZIP_64, stream_zip  # pyre-fixme[21]

from routes.audiobook.schema import (
    AudioSettings,
    Book,
    Chapter,
    book_table,
    chapter_table,
    db,
    minio_client,
    normalize_filename,
    normalize_title,
)
from routes.audiobook.temp_generate_tts import get_supported_voices
from routes.cookies_and_guards import get_user_settings, owns_book_guard
from routes.login_logout import TwitchUser, get_twitch_user, logged_into_twitch_guard


class MyAudiobookBookRoute(Controller):
    path = "/audiobook"
    guards = [logged_into_twitch_guard]
    dependencies = {
        "twitch_user": Provide(get_twitch_user),
    }

    @get("/book/{book_id: int}", dependencies={"user_settings": Provide(get_user_settings)}, guards=[owns_book_guard])
    async def get_book_by_id(
        self,
        twitch_user: TwitchUser,
        user_settings: AudioSettings,
        book_id: int,
    ) -> Template:
        # TODO Why does this load so slowly sometimes? Long queries?
        entry_book_dict: OrderedDict = book_table.find_one(id=book_id, uploaded_by=twitch_user.display_name)
        entry_book: Book = Book.model_validate(entry_book_dict)
        chapters_entries: list[OrderedDict] = chapter_table.find(book_id=entry_book.id, order_by=["chapter_number"])
        chapters: list[Chapter] = [Chapter.model_validate(entry) for entry in chapters_entries]
        available_voices = await get_supported_voices()
        return Template(
            template_name="audiobook/epub_book.html",
            context={
                "user_settings": user_settings,
                "book_id": entry_book.id,
                "book_name": entry_book.book_title.title(),
                "book_author": entry_book.book_author,
                "available_voices": available_voices,
                "chapters": [
                    {
                        "chapter_title": normalize_title(chapter.chapter_title),
                        "chapter_number": chapter.chapter_number,
                        "word_count": chapter.word_count,
                        "sentence_count": chapter.sentence_count,
                        "has_audio": bool(chapter.minio_object_name),
                        "queued": chapter.queued,
                        "position_in_queue": chapter.position_in_queue,
                    }
                    for chapter in chapters
                ],
            },
        )

    @post(
        "/generate_audio",
        guards=[owns_book_guard],
    )
    async def generate_audio(
        self,
        book_id: int,
        chapter_number: int,
        data: Annotated[AudioSettings, Body(media_type=RequestEncodingType.URL_ENCODED)],
        wait_time_for_next_poll: int = 10,
    ) -> Template:
        """
        Implementation of what happens when user clicks "generate audio" button

        Display spinner for user?
        in backend: add task to generate audio
        once audio has been generated: function returns audio as mp3_b64_data
        """
        # Queue chapter to be parsed and generate audio for it
        # Then wait till the job is done before returning

        # Queue the chapter to the database
        entry: OrderedDict = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)
        chapter: Chapter = Chapter.model_validate(entry)
        if chapter.queued is None:
            chapter.audio_settings = data
            chapter.queued = datetime.datetime.now(datetime.timezone.utc)
            chapter_table.update(chapter.model_dump(), keys=["id"])
        return Template(
            template_name="audiobook/epub_chapter.html",
            context={
                "book_id": book_id,
                "wait_time_for_next_poll": wait_time_for_next_poll * 2,
                "chapter": {
                    "chapter_title": chapter.chapter_title,
                    "chapter_number": chapter_number,
                    "has_audio": bool(chapter.minio_object_name),
                    "queued": chapter.queued,
                    "position_in_queue": chapter.position_in_queue,
                },
            },
        )

    @post(
        "/load_generated_audio",
        guards=[owns_book_guard],
    )
    async def load_generated_audio(
        self,
        book_id: int,
        chapter_number: int,
    ) -> Template:
        # Audio has been generated
        entry: OrderedDict = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)
        chapter = Chapter.model_validate(entry)
        return Template(
            template_name="audiobook/epub_chapter.html",
            context={
                "book_id": book_id,
                "chapter": {
                    "mp3_b64_data": chapter.audio_data_b64,
                    "chapter_title": chapter.chapter_title,
                    "chapter_number": chapter_number,
                    "has_audio": bool(chapter.minio_object_name),
                    "queued": chapter.queued,
                },
            },
        )

    @get("/download_chapter_mp3", guards=[owns_book_guard])
    async def download_mp3(
        self,
        book_id: int,
        chapter_number: int,
    ) -> Stream:
        """
        From db: fetch generated audio bytes, stream / download to user
        """
        entry: OrderedDict = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)
        chapter = Chapter.model_validate(entry)
        bytes_data: bytes = chapter.audio_data
        stepsize = 2**20  # 1mb
        content_iterator = (bytes_data[i : i + stepsize] for i in range(0, len(bytes_data), stepsize))
        return Stream(
            content=content_iterator,
            headers={
                # Change file name
                "Content-Disposition": f"attachment; filename={normalize_filename(chapter.chapter_title)}.mp3",
                "Content-Type": "application/mp3",
                # Preview of file size
                "Content-Length": f"{len(bytes_data)}",
            },
            media_type="audio/mpeg",
        )

    @post(
        "generate_audio_book",
        guards=[owns_book_guard],
    )
    async def generate_audio_book(
        self,
        twitch_user: TwitchUser,
        book_id: int,
        data: Annotated[AudioSettings, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> ClientRefresh:
        """
        Generate audio for all chapters
        """
        book_entry: OrderedDict = book_table.find_one(id=book_id, uploaded_by=twitch_user.display_name)
        book = Book.model_validate(book_entry)
        entries = [
            {
                "id": c["id"],
                "audio_settings": data.model_dump(),
                "queued": datetime.datetime.now(datetime.timezone.utc),
            }
            for c in chapter_table.find(book_id=book.id, queued=None, order_by=["chapter_number"])
        ]
        if len(entries) > 0:
            chapter_table.update_many(entries, keys=["id"])
        return ClientRefresh()

    @get(
        "/download_book_zip",
        media_type=MediaType.TEXT,
        sync_to_thread=os.getenv("STAGE") != "test",
        guards=[owns_book_guard],
    )
    def download_book_zip(
        self,
        book_id: int,
        twitch_user: TwitchUser,
    ) -> Stream:
        """
        If all chapters have generated audio:

        create zip from all chapters, make download available to user
        """
        book_entry: OrderedDict = book_table.find_one(id=book_id, uploaded_by=twitch_user.display_name)
        book = Book.model_validate(book_entry)

        # Wait for book audio to be generated
        total_count = chapter_table.count(book_id=book_id)
        while 1:
            done_count: int = chapter_table.count(book_id=book_id, minio_object_name={"!=": None})
            if done_count >= total_count:
                break
            time.sleep(5)

        normalized_author = f"{normalize_title(book.book_author)}"[:50].strip()
        normalized_book_title = f"{normalize_title(book.book_title)}"[:150].strip()

        # Zip files via iterator to use the least amount of memory
        # https://stream-zip.docs.trade.gov.uk/
        # https://stream-zip.docs.trade.gov.uk/get-started/
        def member_files():
            nonlocal normalized_author, normalized_book_title
            modified_at = datetime.datetime.now(datetime.timezone.utc)
            mode = S_IFREG | 0o600
            for chapter_number in range(1, book.chapter_count + 1):
                entry: OrderedDict = chapter_table.find_one(book_id=book.id, chapter_number=chapter_number)
                chapter: Chapter = Chapter.model_validate(entry)
                normalized_chapter_name = normalize_filename(chapter.chapter_title)[:200].strip()
                audio_file_name = (
                    f"{normalized_author}/{normalized_book_title}/{chapter_number:04d}_{normalized_chapter_name}.mp3"
                )
                yield (audio_file_name, modified_at, mode, ZIP_64, (chapter.audio_data,))

        zipped_chunks = stream_zip(member_files(), chunk_size=2**20)

        zip_file_name = f"{normalized_author} - {normalized_book_title}.zip"
        return Stream(
            content=zipped_chunks,
            headers={
                # Change file name
                "Content-Disposition": f"attachment; filename={zip_file_name}",  # noqa: E501
                "Content-Type": "application/zip",
                # Preview of file size
                # "Content-Length": f"{len(bytes_data)}",
                # Unsure what these are for
                "Accept-Encoding": "identity",
                "Content-Transfer-Encoding": "Binary",
            },
        )

    @post("/delete_book", guards=[owns_book_guard])
    async def delete_book(
        self,
        twitch_user: TwitchUser,
        book_id: int,
    ) -> ClientRedirect:
        """
        remove book and all chapters from db
        """
        with db:
            for entry in chapter_table.find(book_id=book_id):
                chapter: Chapter = Chapter.model_validate(entry)
                if chapter.minio_object_name is not None:
                    # pyre-fixme[6]
                    minio_client.remove_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), chapter.minio_object_name)
            chapter_table.delete(book_id=book_id)
            book_table.delete(id=book_id, uploaded_by=twitch_user.display_name)
        return ClientRedirect("/audiobook")

    @post("/delete_generated_audio", guards=[owns_book_guard])
    async def delete_generated_audio(
        self,
        book_id: int,
        chapter_number: int,
    ) -> Template:
        """
        remove generated audio from db
        """
        entry: OrderedDict = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)
        chapter: Chapter = Chapter.model_validate(entry)
        if chapter.queued is not None:
            if chapter.minio_object_name is not None:
                # pyre-fixme[6]
                minio_client.remove_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), chapter.minio_object_name)
                chapter.minio_object_name = None
            chapter.queued = None
            chapter.converting = None
            # pyre-fixme[20]
            chapter.audio_settings = AudioSettings()
            chapter_table.update(chapter.model_dump(), keys=["id"])
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
