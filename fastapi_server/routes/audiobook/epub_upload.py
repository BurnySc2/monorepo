from __future__ import annotations

import datetime
import io
import os
from collections import OrderedDict
from typing import Annotated

from dotenv import load_dotenv
from litestar import Controller, get, post
from litestar.contrib.htmx.response import ClientRedirect
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.params import Body
from litestar.response import Template

from routes.audiobook.schema import (
    Book,
    Chapter,
    book_table,
    chapter_table,
    db,
)
from routes.audiobook.temp_read_epub import (
    EpubChapter,
    EpubMetadata,
    extract_chapters,
    extract_metadata,
)
from routes.login_logout import TwitchUser, get_twitch_user, logged_into_twitch_guard

# TODO Background function that removes all books and chapters that are older than 1 week

load_dotenv()


class MyAudiobookEpubRoute(Controller):
    path = "/audiobook"
    guards = [logged_into_twitch_guard]
    dependencies = {
        "twitch_user": Provide(get_twitch_user),
    }

    @get("/epub_upload")
    async def index(
        self,
        twitch_user: TwitchUser | None,
    ) -> Template:
        # TODO The endpoint "/" should list all uploaded books by user, then be able to navigate to it
        # TODO List all uploaded books
        return Template(template_name="audiobook/epub_upload.html")

    @post("/epub_upload", media_type=MediaType.TEXT, sync_to_thread=os.getenv("STAGE") != "test")
    def file_upload(
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
        epub_data: io.BytesIO = io.BytesIO(data.file.read())

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
                f"/audiobook/book/{entry['id']}",
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

            # Columns that may contain null values but aren't of type string
            chapter_table.create_column_by_example("queued", datetime.datetime.now(datetime.timezone.utc))
            chapter_table.create_column_by_example("converting", datetime.datetime.now(datetime.timezone.utc))

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
                # TODO Use insert many instead
                chapter_table.insert(chapter_dict)
            # Create index to speed up selects
            book_table.create_index(["uploaded_by"])
            chapter_table.create_index(["book_id", "chapter_number"])
        return ClientRedirect(
            f"/audiobook/book/{entry_id}",
        )
