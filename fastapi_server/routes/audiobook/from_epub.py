from __future__ import annotations

import asyncio
import base64
import datetime
import io
from collections import OrderedDict
from typing import Annotated

from litestar import Controller, MediaType, get, post
from litestar.connection import ASGIConnection
from litestar.contrib.htmx.response import (
    ClientRedirect,
)
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.params import Body
from litestar.response import Redirect, Stream, Template
from loguru import logger

from routes.audiobook.schema import Book, Chapter, book_table, chapter_table, db
from routes.audiobook.temp_generate_tts import generate_text_to_speech, get_supported_voices
from routes.audiobook.temp_read_epub import (
    EpubMetadata,
    extract_chapters,
    extract_metadata,
)
from routes.login_logout import COOKIES, TwitchUser, get_twitch_user, logged_into_twitch_guard


def convert_mp3_to_base64_audio(mp3_data: io.BytesIO) -> str:
    """Base64 encode to allow usage in frontend audio players"""
    b64encoded = base64.b64encode(mp3_data).decode("utf-8")
    return b64encoded


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
        chapter = chapter_table.find_one(has_audio=False, queued={"!=": None}, order_by=["queued"])

        # Generate tts from the book
        pages = chapter["content"]["content"]
        # Text still contains "\n" characters
        chapter_text = " ".join(sentence.replace("\n", " ") for page in pages for sentence in page)
        # TODO Why are only 1 second long clips generated?!
        audio: io.BytesIO = await generate_text_to_speech(chapter_text, voice="en-GB-SoniaNeural")

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
    # twitch_user: TwitchUser | None,
) -> None:
    twitch_user = await get_twitch_user(connection.cookies.get(COOKIES["twitch"]))
    book_id = connection.path_params.get("book_id") or connection.query_params["book_id"]
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
    ) -> Redirect:
        """
        This method is responsible for handling the file upload request for EPUB files.
        """
        # TODO disable upload if user has already uploaded too much
        # TODO limit file size
        content: bytes = await data.read()
        data = io.BytesIO(content)

        metadata: EpubMetadata = extract_metadata(data)

        # If not present in database, add book entry
        entry: OrderedDict | None = book_table.find_one(
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

        chapters = extract_chapters(data)
        # Insert book
        my_book = Book(
            uploaded_by=twitch_user.display_name,
            book_title=metadata.title,
            book_author=metadata.author,
            chapter_count=len(chapters),
            # data=data.getvalue(),
            upload_date=datetime.datetime.now(datetime.UTC),
        )
        my_dict = my_book.to_dict()

        with db:
            entry_id = book_table.insert(my_dict)

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
                )
                chapter_dict = my_chapter.model_dump(exclude=["id"])
                chapter_table.insert(chapter_dict)
        return ClientRedirect(
            f"/twitch/audiobook/epub/book/{entry_id}",
        )

    @get("/book/{book_id: int}", guards=[owns_book_guard])
    async def get_book_by_id(
        self,
        twitch_user: TwitchUser,
        book_id: int,
    ) -> Template:
        entry_book_dict: OrderedDict = book_table.find_one(id=book_id, uploaded_by=twitch_user.display_name)
        entry_book: Book = Book(**entry_book_dict)
        chapters: list[Chapter] = Chapter.get_metadata(book_id=entry_book.id)
        available_voices = await get_supported_voices()
        return Template(
            template_name="audiobook/epub_book.html",
            context={
                "book_id": entry_book.id,
                "book_name": entry_book.book_title,
                "book_author": entry_book.book_author,
                "available_voices": available_voices,
                "chapters": [
                    {
                        "chapter_number": chapter.chapter_number,
                        "name": chapter.chapter_title,
                        "word_count": chapter.word_count,
                        "sentence_count": chapter.sentence_count,
                        "has_audio": chapter.has_audio,  # TODO
                        # "has_audio": bool(random.randint(0, 1)),
                        # TODO If chapter has audio: add mp4_b64_data, see new_audio.html
                        # TODO Add "delete" audio button to generate again with another voice
                    }
                    for chapter in chapters
                ],
            },
        )

    @post("/generate_audio", sync_to_thread=True, guards=[owns_book_guard])
    def generate_audio(
        self,
        book_id: int,
        chapter_number: int,
    ) -> Template:
        # TODO Guard: user uploaded the book
        """
        Implementation of what happens when user clicks "generate audio" button

        Display spinner for user?
        in backend: add task to generate audio
        once audio has been generated: function returns audio as mp3_b64_data
        """
        # Queue chapter to be parsed and generate audio for it
        # Then wait till the job is done before returning

        # Queue the chapter to the database
        Chapter.queue_chapter_to_be_generated(book_id=book_id, chapter_number=chapter_number)

        Chapter.wait_for_audio_to_be_generated(book_id, chapter_number)

        # Audio has been generated
        entry: Chapter = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)

        # audio_data: bytes = Book.decode_data(entry.audio_data)
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
        entry: Chapter = chapter_table.find_one(book_id=book_id, chapter_number=chapter_number)
        data = Book.decode_data(entry["audio_data"])
        byte_stream = io.BytesIO(data)
        return Stream(content=byte_stream)

    @post("generate_audio_book", guards=[owns_book_guard])
    async def generate_audio_book(
        self,
        twitch_user: TwitchUser,
        book_id: int,
    ) -> None:
        """
        If all chapters have generated audio:

        create zip from all chapters, make download available to user
        """
        pass

    @post("/download_book_zip", guards=[owns_book_guard])
    async def download_book_zip(
        self,
        twitch_user: TwitchUser,
        book_id: int,
    ) -> None:
        """
        If all chapters have generated audio:

        create zip from all chapters, make download available to user
        """
        pass

    @post("/delete_book", guards=[owns_book_guard])
    async def delete_book(
        self,
        twitch_user: TwitchUser,
        book_id: int,
    ) -> None:
        # TODO Guard: user uploaded the book
        """
        remove book and all chapters from db
        """
        pass

    @post("/delete_generated_audio", guards=[owns_book_guard])
    async def delete_generated_audio(
        self,
        twitch_user: TwitchUser,
        book_id: int,
        chapter_number: int,
    ) -> None:
        # TODO Guard: user uploaded the book
        """
        remove generated audio from db
        """
        pass
