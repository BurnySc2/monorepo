from __future__ import annotations

import asyncio
import os
import re
from stat import S_IFREG
from typing import Annotated

import arrow
from litestar import Controller, Request, Response, get, post
from litestar.contrib.htmx.response import ClientRedirect, ClientRefresh
from litestar.datastructures import Cookie
from litestar.di import Provide
from litestar.enums import MediaType, RequestEncodingType
from litestar.params import Body
from litestar.response import Stream, Template
from minio.helpers import _BUCKET_NAME_REGEX
from stream_zip import ZIP_64, async_stream_zip

from prisma import models
from src.routes.audiobook.schema import (
    AudioSettings,
    base64_encode_data,
    get_chapter_position_in_queue,
    minio_client,
    minio_get_audio_of_chapter,
    normalize_filename,
    normalize_title,
)
from src.routes.audiobook.temp_generate_tts import get_supported_voices
from src.routes.caches import get_db
from src.routes.cookies_and_guards import (
    LoggedInUser,
    get_user_settings,
    is_logged_in_guard,
    owns_book_guard,
    provide_logged_in_user,
)

# pyre-fixme[9]
MINIO_AUDIOBOOK_BUCKET: str = os.getenv("MINIO_AUDIOBOOK_BUCKET")
assert MINIO_AUDIOBOOK_BUCKET is not None
assert re.match(_BUCKET_NAME_REGEX, MINIO_AUDIOBOOK_BUCKET) is not None


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
        async with get_db() as db:
            book = await db.audiobookbook.find_first_or_raise(
                where={
                    "id": book_id,
                    "uploaded_by": logged_in_user.db_name,
                },
                # pyre-fixme[55]
                include={"AudiobookChapter": {"order_by": {"chapter_number": "asc"}}},
            )
            chapters_in_queue: list[dict] = await db.query_raw(
                """
SELECT
	ROW_NUMBER() OVER (ORDER BY queued) - 1 AS row_number,
	id AS chapter_id
FROM
	litestar_audiobook_chapter
WHERE
	litestar_audiobook_chapter.minio_object_name IS NULL
	AND litestar_audiobook_chapter.queued IS NOT NULL
                """
            )
        chapter_id_to_queued_index: dict[int, int] = {row["chapter_id"]: row["row_number"] for row in chapters_in_queue}
        available_voices = await get_supported_voices()
        return Template(
            template_name="audiobook/epub_book.html",
            context={
                "user_settings": user_settings,
                "book_id": book.id,
                "book_name": book.book_title.title(),
                "book_author": book.book_author,
                "available_voices": available_voices,
                "chapters": [
                    {
                        "chapter_title": normalize_title(chapter.chapter_title),
                        "chapter_number": chapter.chapter_number,
                        "word_count": chapter.word_count,
                        "sentence_count": chapter.sentence_count,
                        "has_audio": bool(chapter.minio_object_name),
                        "queued": chapter.queued,
                        "position_in_queue": chapter_id_to_queued_index.get(chapter.id, -1),
                    }
                    for chapter in book.AudiobookChapter
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
        Implementation of what happens when user clicks "generate audio" button.
        """
        # Queue chapter to be parsed and generate audio for it
        # Then wait till the job is done before returning

        # Queue the chapter to the database
        async with get_db() as db:
            chapter = await db.audiobookchapter.find_first_or_raise(
                where={"book_id": book_id, "chapter_number": chapter_number}
            )
            if chapter.queued is None:
                await db.audiobookchapter.update_many(
                    where={"id": chapter.id},
                    data={
                        "audio_settings": data.model_dump_json(),
                        "queued": arrow.utcnow().datetime,
                    },
                )
                # This only updates the attribute locally to render the template correctly
                chapter.queued = arrow.utcnow().datetime

        # TODO Instead of polling on each chapter, have one global poller which updates all chapters with one query
        # and oob-swaps instead.
        # It needs to have a state of ids that need to be polled.
        # Remove global poller when there is nothing left to poll
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
                    "position_in_queue": await get_chapter_position_in_queue(chapter),
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
        async with get_db() as db:
            chapter = await db.audiobookchapter.find_first_or_raise(
                where={
                    "book_id": book_id,
                    "chapter_number": chapter_number,
                }
            )
        return Template(
            template_name="audiobook/epub_chapter.html",
            context={
                "book_id": book_id,
                "chapter": {
                    "mp3_b64_data": base64_encode_data(await minio_get_audio_of_chapter(chapter)),
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
        async with get_db() as db:
            chapter = await db.audiobookchapter.find_first_or_raise(
                where={
                    "book_id": book_id,
                    "chapter_number": chapter_number,
                }
            )
        bytes_data: bytes = await minio_get_audio_of_chapter(chapter)
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
        logged_in_user: LoggedInUser,
        book_id: int,
        data: Annotated[AudioSettings, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> ClientRefresh:
        """
        Generate audio for all chapters
        """
        async with get_db() as db:
            chapters = await db.audiobookchapter.find_many(
                where={
                    "book_id": book_id,
                    # pyre-fixme[55]
                    "book": {"uploaded_by": logged_in_user.db_name},
                    "queued": None,
                },
                order=[{"chapter_number": "asc"}],
            )
            async with db.batch_() as batcher:
                for chapter in chapters:
                    batcher.audiobookchapter.update(
                        where={"id": chapter.id},
                        data={
                            "audio_settings": data.model_dump_json(),
                            "queued": arrow.utcnow().datetime,
                        },
                    )
                    # await db.audiobookchapter.update_many(
                    #     where={"id": chapter.id},
                    # )
                await batcher.commit()
        return ClientRefresh()

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
        async with get_db() as db:
            book = await db.audiobookbook.find_first_or_raise(
                where={
                    "id": book_id,
                    "uploaded_by": logged_in_user.db_name,
                }
            )

        # Wait for book audio to be generated
        total_count = book.chapter_count
        for _ in range(60):
            async with get_db() as db:
                done_count: int = await db.audiobookchapter.count(
                    # pyre-fixme[55]
                    where={
                        "book_id": book_id,
                        "minio_object_name": {
                            "not": None,
                        },
                    }
                )
            if done_count >= total_count:
                break
            await asyncio.sleep(5)
        else:
            # No "break" has been encountered, which means the audio has not been successfully generated
            return None

        normalized_author = f"{normalize_title(book.book_author)}"[:50].strip()
        normalized_book_title = f"{normalize_title(book.book_title)}"[:150].strip()

        async with get_db() as db:
            book = await db.audiobookbook.find_first_or_raise(
                where={
                    "id": book_id,
                    "uploaded_by": logged_in_user.db_name,
                },
                include={"AudiobookChapter": {"order_by": [{"chapter_number": "asc"}]}},
            )

        # Zip files via iterator to use the least amount of memory
        # https://stream-zip.docs.trade.gov.uk/
        # https://stream-zip.docs.trade.gov.uk/get-started/
        # https://stream-zip.docs.trade.gov.uk/async-interface/
        async def async_data(chapter: models.AudiobookChapter):
            yield await minio_get_audio_of_chapter(chapter)

        async def member_files():
            nonlocal normalized_author, normalized_book_title
            modified_at = arrow.utcnow().datetime
            mode = S_IFREG | 0o600
            for chapter in book.AudiobookChapter:
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

        def delete_minio_objects(bucket_name: str, object_names: list[str]) -> None:
            # minio_client.remove_objects does not work
            for minio_object_name in object_names:
                minio_client.remove_object(bucket_name, minio_object_name)

        async with get_db() as db:
            # pyre-fixme[55]
            chapters = await db.audiobookchapter.find_many(where={"minio_object_name": {"not": None}})
            chapter_objects_to_remove = [
                chapter.minio_object_name for chapter in chapters if chapter.minio_object_name is not None
            ]
            await asyncio.to_thread(delete_minio_objects, MINIO_AUDIOBOOK_BUCKET, chapter_objects_to_remove)
            await db.audiobookbook.delete_many(where={"id": book_id, "uploaded_by": logged_in_user.db_name})

        # hx-remove table row if origin path is overview of uploaded books
        # pyre-fixme[16]
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
        async with get_db() as db:
            chapter = await db.audiobookchapter.find_first_or_raise(
                where={"book_id": book_id, "chapter_number": chapter_number}
            )
            if chapter.minio_object_name is not None:
                minio_client.remove_object(MINIO_AUDIOBOOK_BUCKET, chapter.minio_object_name)
            await db.audiobookchapter.update_many(
                where={"id": chapter.id},
                data={
                    "queued": None,
                    "started_converting": None,
                    "minio_object_name": None,
                    "audio_settings": "{}",
                },
            )
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
