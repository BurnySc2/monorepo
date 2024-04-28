from __future__ import annotations

import asyncio
import datetime
import io
import json
import re
import zipfile
from collections import OrderedDict
from typing import Annotated

from litestar import Controller, Response, get, post
from litestar.connection import ASGIConnection
from litestar.contrib.htmx.response import (
    ClientRedirect,
)
from litestar.datastructures import Cookie, UploadFile
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.params import Body, Parameter
from litestar.response import Stream, Template
from loguru import logger
from pydantic import BaseModel

from routes.audiobook.schema import Book, Chapter, book_table, chapter_table, db
from routes.audiobook.temp_generate_tts import generate_text_to_speech, get_supported_voices
from routes.audiobook.temp_read_epub import (
    EpubChapter,
    EpubMetadata,
    extract_chapters,
    extract_metadata,
)
from routes.login_logout import COOKIES, TwitchUser, get_twitch_user, logged_into_twitch_guard


def normalize_filename(filename: str) -> str:
    # Replace any character that is not alphanumeric or underscore with an underscore
    normalized_filename = re.sub(r"[^\w]", "_", filename)
    # Replace two or more underscores with one underscore
    normalized_filename = re.sub(r"_+", "_", normalized_filename)
    # Remove underscores from the start and end
    return normalized_filename.strip("_")


# pyre-fixme[13]
class AudioSettings(BaseModel):
    voice_name: str
    voice_rate: int
    voice_volume: int
    voice_pitch: int


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
    while 1:
        # Check if queue empty
        any_in_queue = chapter_table.count(has_audio=False, queued={"!=": None})
        if any_in_queue == 0:
            # Skip / wait
            # TODO Change to 60?
            await asyncio.sleep(10)
            continue

        # Get first book that is waiting to be converted
        logger.info("Converting text to audio...")
        chapter: OrderedDict = chapter_table.find_one(has_audio=False, queued={"!=": None}, order_by=["queued"])
        audio_settings: AudioSettings = AudioSettings.model_validate(json.loads(chapter["audio_settings"]))

        # Generate tts from the book
        pages = chapter["content"]["content"]
        # Text still contains "\n" characters
        chapter_text = " ".join(sentence for page in pages for sentence in page)
        audio: io.BytesIO = await generate_text_to_speech(
            chapter_text,
            voice=audio_settings.voice_name,
            rate=audio_settings.voice_rate,
            volume=audio_settings.voice_volume,
            pitch=audio_settings.voice_pitch,
        )

        # Save result to database
        logger.info("Saving result to database")
        chapter_table.update(
            chapter
            | {
                "audio_data": Book.encode_data(audio.getvalue()),
                "has_audio": True,
            },
            keys=["id"],
        )
        logger.info("Done converting")


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

        # Act as transaction to only insert full book and chapters

        chapters: list[EpubChapter] = extract_chapters(epub_data)
        # Insert book
        my_book = Book(
            uploaded_by=twitch_user.display_name,
            book_title=metadata.title,
            book_author=metadata.author,
            chapter_count=len(chapters),
            # data=data.getvalue(),
            upload_date=datetime.datetime.now(datetime.timezone.utc),
        )
        with db:
            # pyre-fixme[6]
            entry_id = book_table.insert(my_book.model_dump(exclude=["id"]))

            # Parse and insert chapters
            for chapter in chapters:
                my_chapter: Chapter = Chapter(
                    book_id=entry_id,
                    chapter_title=chapter.chapter_title,
                    chapter_number=chapter.chapter_number,
                    word_count=chapter.word_count,
                    sentence_count=chapter.sentence_count,
                    content={"content": chapter.content},
                    has_audio=False,
                    audio_settings="{}",
                )
                # pyre-fixme[6]
                chapter_dict = my_chapter.model_dump(exclude=["id"])
                chapter_table.insert(chapter_dict)
            chapter_table.create_column_by_example("queued", datetime.datetime.now(datetime.timezone.utc))
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
        entry_book_dict: OrderedDict = book_table.find_one(id=book_id, uploaded_by=twitch_user.display_name)
        entry_book: Book = Book.model_validate(entry_book_dict)
        # pyre-fixme[6]
        chapters: list[Chapter] = Chapter.get_metadata(book_id=entry_book.id)
        available_voices = await get_supported_voices()
        return Template(
            template_name="audiobook/epub_book.html",
            context={
                "user_settings": user_settings,
                "book_id": entry_book.id,
                "book_name": entry_book.book_title,
                "book_name_zip": normalize_filename(entry_book.book_title),
                "book_author": entry_book.book_author,
                "available_voices": available_voices,
                "chapters": [
                    {
                        "chapter_number": chapter.chapter_number,
                        "name": chapter.chapter_title,
                        "word_count": chapter.word_count,
                        "sentence_count": chapter.sentence_count,
                        "has_audio": chapter.has_audio,  # TODO
                        # TODO If chapter has audio: add mp4_b64_data, see new_audio.html
                        # TODO Add "delete" audio button to generate again with another voice
                    }
                    for chapter in chapters
                ],
            },
        )

    @post(
        "/generate_audio",
        sync_to_thread=True,
        dependencies={"user_settings": Provide(get_user_settings)},
        guards=[owns_book_guard],
    )
    def generate_audio(
        self,
        book_id: int,
        chapter_number: int,
        user_settings: AudioSettings,
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
        Chapter.queue_chapter_to_be_generated(
            book_id=book_id,
            chapter_number=chapter_number,
            audio_settings=user_settings.model_dump(),
        )

        Chapter.wait_for_audio_to_be_generated(book_id, chapter_number)

        # Audio has been generated
        entry: OrderedDict = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)
        # TODO Could return earli with a template and let htmx do the polling

        return Template(
            template_name="audiobook/audio_player.html",
            context={
                "mp3_b64_data": entry["audio_data"],
                "chapter_title": entry["chapter_title"],
                "book_id": book_id,
                "chapter_number": chapter_number,
            },
        )

    @get("/download_chapter_mp3", sync_to_thread=True, media_type=MediaType.TEXT, guards=[owns_book_guard])
    def download_mp3(
        self,
        book_id: int,
        chapter_number: int,
    ) -> Stream:
        """
        From db: fetch generated audio bytes, stream / download to user
        """
        entry: OrderedDict = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)
        data = Book.decode_data(entry["audio_data"])
        byte_stream = io.BytesIO(data)
        return Stream(content=byte_stream)

    @post(
        "generate_audio_book",
        dependencies={"user_settings": Provide(get_user_settings)},
        guards=[owns_book_guard],
        sync_to_thread=True,
    )
    def generate_audio_book(
        self,
        twitch_user: TwitchUser,
        book_id: int,
        user_settings: AudioSettings,
    ) -> ClientRedirect:
        """
        Generate audio for all chapters
        """
        book_entry: OrderedDict = book_table.find_one(id=book_id, uploaded_by=twitch_user.display_name)
        book = Book.model_validate(book_entry)
        # TODO Use one query instead of for loop
        for chapter_number in range(1, book.chapter_count + 1):
            # pyre-fixme[6]
            Chapter.queue_chapter_to_be_generated(book.id, chapter_number, audio_settings=user_settings.model_dump())
        # TODO Use one query instead of for loop
        for chapter_number in range(1, book.chapter_count + 1):
            # pyre-fixme[6]
            Chapter.wait_for_audio_to_be_generated(book.id, chapter_number)
        return ClientRedirect(f"/twitch/audiobook/epub/book/{book.id}")

    @get("/download_book_zip", sync_to_thread=True, guards=[owns_book_guard])
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
        for chapter_number in range(1, book.chapter_count + 1):
            # pyre-fixme[6]
            Chapter.wait_for_audio_to_be_generated(book.id, chapter_number)

        audio_data = {}
        for chapter_number in range(1, book.chapter_count + 1):
            entry: OrderedDict = chapter_table.find_one(book_id=book.id, chapter_number=chapter_number)
            entry["queued"] = None
            chapter = Chapter.model_validate(entry)
            normalized_chapter_name = normalize_filename(chapter.chapter_title)
            audio_file_name = f"{chapter_number:04d}_{normalized_chapter_name}.mp3"
            # pyre-fixme[6]
            audio_data[audio_file_name] = Book.decode_data(chapter.audio_data)

        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_name, content in audio_data.items():
                zipf.writestr(file_name, content)
        zip_buffer.seek(0)  # Required?
        return Stream(content=zip_buffer)

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
                Cookie(key="voice_name", value=data.voice_name, path="/"),
                Cookie(key="voice_rate", value=str(data.voice_rate), path="/"),
                Cookie(key="voice_volume", value=str(data.voice_volume), path="/"),
                Cookie(key="voice_pitch", value=str(data.voice_pitch), path="/"),
            ],
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
        Chapter.delete_audio(book_id=book_id, chapter_number=chapter_number)
        return Template(
            template_name="audiobook/generate_audio_button.html",
            context={
                "book_id": book_id,
                "chapter_number": chapter_number,
            },
        )
