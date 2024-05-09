from __future__ import annotations

import asyncio
import datetime
import io
import time
from collections import OrderedDict
from pathlib import Path
from stat import S_IFREG
from typing import Annotated

from litestar import Controller, Response, get, post
from litestar.connection import ASGIConnection
from litestar.contrib.htmx.response import ClientRedirect, ClientRefresh
from litestar.datastructures import Cookie, UploadFile
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.params import Body, Parameter
from litestar.response import Stream, Template
from loguru import logger
from stream_zip import ZIP_64, stream_zip  # pyre-fixme[21]

from routes.audiobook.schema import (
    AudioSettings,
    Book,
    Chapter,
    book_table,
    chapter_table,
    db,
    normalize_filename,
    normalize_title,
)
from routes.audiobook.temp_generate_tts import generate_text_to_speech, get_supported_voices
from routes.audiobook.temp_read_epub import (
    EpubChapter,
    EpubMetadata,
    extract_chapters,
    extract_metadata,
)
from routes.login_logout import COOKIES, TwitchUser, get_twitch_user, logged_into_twitch_guard

AUDIOBOOK_MP3_FOLDER = Path(__file__).parents[2] / "data/audiobook_mp3"


async def get_user_settings(
    voice_name: Annotated[str | None, Parameter(cookie="voice_name")] = None,
    voice_rate: Annotated[int | None, Parameter(cookie="voice_rate")] = None,
    voice_volume: Annotated[int | None, Parameter(cookie="voice_volume")] = None,
    voice_pitch: Annotated[int | None, Parameter(cookie="voice_pitch")] = None,
) -> AudioSettings:
    available_voices: list[str] = await get_supported_voices()
    return AudioSettings(
        voice_name=voice_name or available_voices[0],
        voice_rate=voice_rate or 0,
        voice_volume=voice_volume or 0,
        voice_pitch=voice_pitch or 0,
    )


# TODO Background function that removes all books and chapters that are older than 1 week


async def background_convert_function() -> None:
    """
    This is a background task that runs in the background.
    It is responsible for converting uploaded EPUB files to MP3 audio files.
    """
    await asyncio.sleep(5)
    logger.info("Background tts converter started!")

    async def convert_one():
        # Get first book that is waiting to be converted
        logger.info("Converting text to audio...")
        chapter_entry: OrderedDict = chapter_table.find_one(
            audio_data_absolute_path=None, queued={"!=": None}, order_by=["queued", "chapter_number"]
        )
        chapter: Chapter = Chapter.model_validate(chapter_entry)

        # Generate tts from the book
        audio_settings: AudioSettings = chapter.audio_settings
        audio: io.BytesIO = await generate_text_to_speech(
            chapter.combined_text,
            voice=audio_settings.voice_name,
            rate=audio_settings.voice_rate,
            volume=audio_settings.voice_volume,
            pitch=audio_settings.voice_pitch,
        )

        # Get data from db, user may have clicked "delete" button on book or chapter
        chapter_entry2: OrderedDict = chapter_table.find_one(id=chapter.id)
        if chapter_entry2 is None:
            # Book was deleted
            return
        chapter2: Chapter = Chapter.model_validate(chapter_entry2)
        if chapter.audio_settings != chapter2.audio_settings:
            # Audio was removed while conversion was in progress
            logger.info("Audio settings mismatch, skipping")
            return

        # Save result to database
        with db:
            audio_data_path = AUDIOBOOK_MP3_FOLDER / f"{chapter.id}_audio.mp3"
            audio_data_path.parent.mkdir(parents=True, exist_ok=True)
            audio_data_path.write_bytes(audio.getvalue())
            chapter.audio_data_absolute_path = str(audio_data_path.absolute())
            logger.info("Saving result to database")
            chapter_table.update(
                chapter.model_dump(),
                keys=["id"],
            )
        logger.info("Done converting")

    while 1:
        # Check if queue empty
        any_in_queue = chapter_table.count(audio_data_absolute_path=None, queued={"!=": None})
        if any_in_queue == 0:
            # Skip / wait
            await asyncio.sleep(5)
            continue

        try:
            await convert_one()
        except Exception as e:  # noqa: BLE001
            logger.exception(e)
            await asyncio.sleep(1)


async def owns_book_guard(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    twitch_user = await get_twitch_user(connection.cookies.get(COOKIES["twitch"]))
    book_id = connection.path_params.get("book_id") or connection.query_params["book_id"]
    # pyre-fixme[16]
    book_count = book_table.count(id=book_id, uploaded_by=twitch_user.display_name)
    if book_count == 0:
        raise NotAuthorizedException("You don't have access to this book.")


class MyAudiobookEpubRoute(Controller):
    path = "/twitch/audiobook/epub"
    guards = [logged_into_twitch_guard]
    dependencies = {
        "twitch_user": Provide(get_twitch_user),
    }

    @get("/")
    async def index(
        self,
        twitch_user: TwitchUser | None,
    ) -> Template:
        # TODO The endpoint "/" should list all uploaded books by user, then be able to navigate to it
        # TODO List all uploaded books
        return Template(template_name="audiobook/epub_upload.html")

    @post("/", media_type=MediaType.TEXT)
    async def file_upload(
        self,
        twitch_user: TwitchUser | None,
        data: Annotated[
            UploadFile,
            Body(media_type=RequestEncodingType.MULTI_PART),
        ],
    ) -> ClientRedirect:
        """
        This method is responsible for handling the file upload request for EPUB files.
        """
        # TODO disable upload if user has already uploaded too much
        # TODO limit file size
        epub_data: io.BytesIO = io.BytesIO(await data.read())

        metadata: EpubMetadata = extract_metadata(epub_data)

        # If not present in database, add book entry
        entry: OrderedDict | None = book_table.find_one(
            # pyre-fixme[16]
            uploaded_by=twitch_user.display_name,
            book_title=metadata.title,
            book_author=metadata.author,
        )
        if entry is not None:
            # Already present
            return ClientRedirect(
                f"/twitch/audiobook/epub/book/{entry['id']}",
            )

        # TODO If user uploaded X books in the last Y days, return error that too many books were uploaded

        chapters: list[EpubChapter] = extract_chapters(epub_data)
        # Insert book
        my_book = Book(
            uploaded_by=twitch_user.display_name,
            book_title=metadata.title,
            book_author=metadata.author,
            chapter_count=len(chapters),
            upload_date=datetime.datetime.now(datetime.timezone.utc),
        )
        # Act as transaction to only insert full book and chapters
        with db:
            entry_id = book_table.insert(my_book.model_dump(exclude=["id"]))

            # Parse and insert chapters
            for chapter in chapters:
                my_chapter: Chapter = Chapter(
                    book_id=entry_id,
                    chapter_title=chapter.chapter_title,
                    chapter_number=chapter.chapter_number,
                    word_count=chapter.word_count,
                    sentence_count=chapter.sentence_count,
                    content=chapter.content,
                )
                chapter_dict = my_chapter.model_dump(exclude=["id"])
                chapter_table.insert(chapter_dict)
            chapter_table.create_column_by_example("audio_data_absolute_path", "some_path")
            chapter_table.create_column_by_example("queued", datetime.datetime.now(datetime.timezone.utc))
            # Create index to speed up selects
            book_table.create_index(["uploaded_by"])
            chapter_table.create_index(["book_id", "chapter_number"])
        return ClientRedirect(
            f"/twitch/audiobook/epub/book/{entry_id}",
        )

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
                        "has_audio": bool(chapter.audio_data_absolute_path),
                        "queued": chapter.queued,
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
                    "has_audio": bool(chapter.audio_data_absolute_path),
                    "queued": chapter.queued,
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
                    "has_audio": bool(chapter.audio_data_absolute_path),
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
        for entry in chapter_table.find(book_id=book.id, queued=None):
            chapter: Chapter = Chapter.model_validate(entry)
            chapter.audio_settings = data
            chapter.queued = datetime.datetime.now(datetime.timezone.utc)
            chapter_table.update(chapter.model_dump(), keys=["id"])
        return ClientRefresh()

    @get("/download_book_zip", media_type=MediaType.TEXT, sync_to_thread=True, guards=[owns_book_guard])
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

        total_count = chapter_table.count(book_id=book_id)
        while 1:
            done_count: int = chapter_table.count(book_id=book_id, audio_data_absolute_path={"!=": None})
            if done_count >= total_count:
                break
            time.sleep(5)

        # Zip files via iterator to use the least amount of memory
        # https://stream-zip.docs.trade.gov.uk/
        # https://stream-zip.docs.trade.gov.uk/get-started/
        def member_files():
            modified_at = datetime.datetime.now(datetime.timezone.utc)
            mode = S_IFREG | 0o600
            normalized_author = f"{normalize_title(book.book_author)}"[:50]
            normalized_book_title = f"{normalize_title(book.book_title)}"[:50]
            for chapter_number in range(1, book.chapter_count + 1):
                entry: OrderedDict = chapter_table.find_one(book_id=book.id, chapter_number=chapter_number)
                chapter: Chapter = Chapter.model_validate(entry)
                normalized_chapter_name = normalize_filename(chapter.chapter_title)[:100]
                audio_file_name = (
                    f"{normalized_author}/{normalized_book_title}/{chapter_number:04d}_{normalized_chapter_name}.mp3"
                )
                yield (audio_file_name, modified_at, mode, ZIP_64, (chapter.audio_data,))

        zipped_chunks = stream_zip(member_files(), chunk_size=2**20)

        zip_file_name = f"{normalize_title(book.book_author)} - {normalize_title(book.book_title)}.zip"
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
                if chapter.audio_data_absolute_path is not None:
                    chapter.audio_data_path.unlink(missing_ok=True)
            chapter_table.delete(book_id=book_id)
            book_table.delete(id=book_id, uploaded_by=twitch_user.display_name)
        return ClientRedirect("/twitch/audiobook/epub")

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
        if chapter.audio_data_absolute_path is not None:
            chapter.audio_data_path.unlink(missing_ok=True)
            chapter.queued = None
            chapter.audio_data_absolute_path = None
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
