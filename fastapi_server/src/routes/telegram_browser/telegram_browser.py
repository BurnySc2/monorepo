from __future__ import annotations

from datetime import timedelta
from typing import Annotated, Literal

import arrow
from litestar import Controller, get, post
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.htmx.response import HTMXTemplate
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Template
from litestar.stores.memory import MemoryStore
from loguru import logger
from pydantic import BaseModel, PositiveInt

from prisma import models
from prisma.enums import Status
from src.routes.caches import get_db
from src.routes.telegram_browser.cookies_and_guards import is_logged_in_allowed_accounts_guard

telegram_store = MemoryStore()


async def all_channels_cache() -> list[models.TelegramChannel]:
    # TODO Use helper-function from caches.py
    all_channels = await telegram_store.get("all_channels")
    if all_channels is None:
        async with get_db() as db:
            all_channels = await db.telegramchannel.find_many(
                where={"channel_username": {"not": None}},
                order={
                    "channel_username": "asc",
                },
            )
        await telegram_store.set("all_channels", all_channels, expires_in=300)  # 5 Minutes
    return await telegram_store.get("all_channels")


async def all_file_formats_cache() -> list[models.TelegramChannel]:
    # TODO Use helper-function from caches.py
    all_file_formats = await telegram_store.get("all_file_formats")
    if all_file_formats is None:
        async with get_db() as db:
            all_file_formats: list[dict] = await db.query_raw(
                """
SELECT DISTINCT LOWER(file_extension) AS file_extension_lower
FROM public.litestar_telegram_message
WHERE file_extension IS NOT NULL
ORDER BY file_extension_lower;
                """
            )
        await telegram_store.set("all_file_formats", all_file_formats, expires_in=300)  # 5 Minutes
    return await telegram_store.get("all_file_formats")


class SearchInput(BaseModel):
    search_text: str  # Contains (case insensitive)
    channel_name: str  # Contains (case insensitive)
    datetime_min: str  # As datetime string which arrow can parse
    datetime_max: str
    # May be "" if field has no value
    comments_min: PositiveInt | Literal[""]
    comments_max: PositiveInt | Literal[""]
    reactions_min: PositiveInt | Literal[""]
    reactions_max: PositiveInt | Literal[""]
    # ATTACHMENT
    must_have_file: bool = False  # Seems to be missing if not checked
    file_extension: str
    file_duration_min: str  # As "01:23:45"
    file_duration_max: str
    file_size_min: PositiveInt | Literal[""]
    file_size_max: PositiveInt | Literal[""]
    file_image_width_min: PositiveInt | Literal[""]
    file_image_width_max: PositiveInt | Literal[""]
    file_image_height_min: PositiveInt | Literal[""]
    file_image_height_max: PositiveInt | Literal[""]


def string_to_seconds(duration: str) -> int:
    """Converts '01:23:45' into seconds."""
    assert duration.count(":") == 2
    hours, minutes, seconds = duration.split(":")
    delta = timedelta(hours=int(hours), minutes=int(minutes), seconds=int(seconds))
    return int(delta.total_seconds())


class MyTelegramBrowserRoute(Controller):
    path = "/telegram-browser"
    guards = [is_logged_in_allowed_accounts_guard]
    request_class = HTMXRequest

    @get("/")
    async def index(
        self,
    ) -> Template:
        # all_channels = await all_channels_cache()
        # all_file_formats = await all_file_formats_cache()
        return Template(
            "telegram_browser/index.html",
            # context={
            #     "channel_names": [i.channel_username for i in all_channels],
            #     "file_extensions": [i["file_extension_lower"] for i in all_file_formats],
            # },
        )

    @post("/search")
    async def query_search(
        self,
        request: HTMXRequest,
        data: Annotated[SearchInput, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        logger.info(f"Search input: {data=}")
        async with get_db() as db:
            results = await db.telegrammessage.find_many(
                # If "{}" then the filter will be ignored
                where={
                    "AND": [
                        # SEARCH TEXT
                        {"message_text": {"contains": data.search_text, "mode": "insensitive"}}
                        if data.search_text
                        else {},
                        # CHANNEL NAME
                        {"channel": {"channel_username": {"contains": data.channel_name, "mode": "insensitive"}}}
                        if data.channel_name
                        else {},
                        # DATE RANGE
                        {"message_date": {"gte": arrow.get(data.datetime_min).datetime}}
                        if data.datetime_min != ""
                        else {},
                        {"message_date": {"lte": arrow.get(data.datetime_max).datetime}}
                        if data.datetime_max != ""
                        else {},
                        # AMOUNT OF REACTIONS
                        {"amount_of_reactions": {"gte": data.reactions_min}} if data.reactions_min != "" else {},
                        {"amount_of_reactions": {"lte": data.reactions_max}} if data.reactions_max != "" else {},
                        # AMOUNT OF COMMENTS
                        {"amount_of_comments": {"gte": data.comments_min}} if data.comments_min != "" else {},
                        {"amount_of_comments": {"lte": data.comments_min}} if data.comments_min != "" else {},
                        # ATTACHMENT
                        # HAS FILE
                        {"status": Status.NoFile} if not data.must_have_file else {},
                        {"status": {"not": Status.NoFile}} if data.must_have_file else {},
                        # HAS FILE
                        {"file_extension": data.file_extension} if data.file_extension != "" else {},
                        # FILE DURATION
                        {"file_duration_seconds": {"gte": string_to_seconds(data.file_duration_min)}}
                        if string_to_seconds(data.file_duration_min) > 0
                        else {},
                        {"file_duration_seconds": {"lte": string_to_seconds(data.file_duration_max)}}
                        if string_to_seconds(data.file_duration_max) > 0
                        else {},
                        # FILE SIZE
                        {"file_size_bytes": {"gte": data.file_size_min}} if data.file_size_min != "" else {},
                        {"file_size_bytes": {"lte": data.file_size_max}} if data.file_size_max != "" else {},
                        # IMAGE SIZE WIDTH
                        {"file_width": {"gte": data.file_image_width_min}} if data.file_image_width_min != "" else {},
                        {"file_width": {"lte": data.file_image_width_max}} if data.file_image_width_max != "" else {},
                        # IMAGE SIZE HEIGHT
                        {"file_height": {"gte": data.file_image_height_min}}
                        if data.file_image_height_min != ""
                        else {},
                        {"file_height": {"lte": data.file_image_height_max}}
                        if data.file_image_height_max != ""
                        else {},
                    ],
                },
                # TODO How to order search? Click on table columns?
                # order={""},
                include={"channel": True},
                take=200,
                skip=0,  # TODO Pagination
            )
        return HTMXTemplate(
            template_name="telegram_browser/search_results.html",
            context={"results": results},
            # TODO Change url to represent search params
            # push_url="/asd",
        )

    @post("/queue-file")
    async def queue_download_file(
        self,
    ) -> Template:
        "In database, set file to queued"

    @post("/delete-file")
    async def delete_file(
        self,
    ) -> Template:
        "Delete file in database and in minio"

    @get("/view-file")
    async def view_file(
        self,
    ) -> Template:
        """
        Allow the user to view the file in browser
        Return <video> element for videos, <audio> for audio, <img> for image
        """

    @get("/download-file")
    async def download_file(
        self,
    ) -> Template:
        "Allow the user to download the file to file system"
