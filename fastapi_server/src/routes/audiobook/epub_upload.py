from __future__ import annotations

import io
from typing import Annotated

from dotenv import load_dotenv
from litestar import Controller, get, post
from litestar.contrib.htmx.response import ClientRedirect
from litestar.datastructures import UploadFile
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.params import Body
from litestar.response import Template

from src.routes.audiobook.temp_read_epub import (
    EpubChapter,
    EpubMetadata,
    extract_chapters,
    extract_metadata,
)
from src.routes.caches import get_db
from src.routes.cookies_and_guards import LoggedInUser, is_logged_in_guard, provide_logged_in_user

load_dotenv()


class MyAudiobookEpubRoute(Controller):
    path = "/audiobook"
    guards = [is_logged_in_guard]
    dependencies = {
        "logged_in_user": Provide(provide_logged_in_user),
    }

    @get("/epub_upload")
    async def index(
        self,
    ) -> Template:
        return Template(template_name="audiobook/epub_upload.html")

    @post("/epub_upload", media_type=MediaType.TEXT)
    async def file_upload(
        self,
        logged_in_user: LoggedInUser,
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
        # TODO Enable pdf upload with "from_pdf.py" - how to detect if uploaded file is in .pdf or .epub format?
        # Raise error on other file formats
        epub_data: io.BytesIO = io.BytesIO(data.file.read())

        metadata: EpubMetadata = extract_metadata(epub_data)

        # If not present in database, add book entry
        async with get_db() as db:
            book = await db.audiobookbook.find_first(
                where={
                    "uploaded_by": logged_in_user.db_name,
                    "book_title": metadata.title,
                    "book_author": metadata.author,
                }
            )
        if book is not None:
            # Already present
            return ClientRedirect(
                f"/audiobook/book/{book.id}",
            )

        # TODO If user uploaded X books in the last Y days, return error that too many books were uploaded

        chapters: list[EpubChapter] = extract_chapters(epub_data)
        # Insert book
        async with get_db() as db:
            book = await db.audiobookbook.create(
                {
                    "uploaded_by": logged_in_user.db_name,
                    "book_title": metadata.title,
                    "book_author": metadata.author,
                    "chapter_count": len(chapters),
                    # pyre-fixme[55]
                    "AudiobookChapter": {
                        "create": [
                            {
                                "chapter_title": chapter.chapter_title,
                                "chapter_number": chapter.chapter_number,
                                "word_count": chapter.word_count,
                                "sentence_count": chapter.sentence_count,
                                "content": chapter.combined_text,
                            }
                            for chapter in chapters
                        ]
                    },
                }
            )
        return ClientRedirect(
            f"/audiobook/book/{book.id}",
        )
