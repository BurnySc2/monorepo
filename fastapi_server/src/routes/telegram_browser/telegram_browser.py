from __future__ import annotations

import json
from datetime import timedelta
from typing import Annotated, Any, Literal

import arrow
import humanize
from litestar import Controller, Response, get, post
from litestar.contrib.htmx.request import HTMXRequest
from litestar.contrib.htmx.response import HTMXTemplate
from litestar.datastructures import Cookie
from litestar.enums import RequestEncodingType
from litestar.params import Body, Parameter
from litestar.response import Template
from litestar.stores.memory import MemoryStore
from loguru import logger
from pydantic import BaseModel, PositiveInt

from prisma import models
from prisma.enums import Status
from src.routes.caches import get_db
from src.routes.telegram_browser.cookies_and_guards import is_logged_in_allowed_accounts_guard

telegram_store = MemoryStore()

COOKIES = {"active_columns": "active-columns"}

RESULT_COLUMNS = {
    # key: column head row name
    "message_link": "Link",
    "message_date": "Date",
    "message_text": "Text",
    "amount_of_reactions": "#Reactions",
    "amount_of_comments": "#Comments",
    "file_extension": "File type",
    "file_size_bytes": "Size",
    "file_duration_seconds": "Duration",
}


async def all_channels_cache() -> list[models.TelegramChannel]:
    # TODO Use helper-function from caches.py
    all_channels = await telegram_store.get("all_channels")
    if all_channels is None:
        async with get_db() as db:
            all_channels = await db.telegramchannel.find_many(
                # pyre-fixme[55]
                where={"channel_username": {"not": None}},
                order={
                    "channel_username": "asc",
                },
            )
        # pyre-fixme[6]
        await telegram_store.set("all_channels", all_channels, expires_in=300)  # 5 Minutes
    # pyre-fixme[7]
    return await telegram_store.get("all_channels")


async def all_file_formats_cache() -> list[models.TelegramChannel]:
    # TODO Use helper-function from caches.py
    all_file_formats: list[dict] = await telegram_store.get("all_file_formats")
    if all_file_formats is None:
        async with get_db() as db:
            all_file_formats = await db.query_raw(
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


def seconds_to_string(duration: float) -> str:
    minutes, seconds = divmod(int(duration), 60)
    hours, minutes = divmod(minutes, 60)
    if hours > 0:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes}:{seconds:02d}"


def get_actived_and_disabled_columns(active_columns_str: str | None) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if active_columns_str is None:
        return RESULT_COLUMNS, {}
    active_columns_list: list[str] = json.loads(active_columns_str)
    active_columns_dict = {key: RESULT_COLUMNS[key] for key in active_columns_list if key in RESULT_COLUMNS}
    disabled_columns_dict = {k: v for k, v in RESULT_COLUMNS.items() if k not in active_columns_dict}
    return active_columns_dict, disabled_columns_dict


class MyTelegramBrowserRoute(Controller):
    path = "/telegram-browser"
    guards = [is_logged_in_allowed_accounts_guard]
    request_class = HTMXRequest

    @get("/")
    async def index(
        self,
        active_columns_str: Annotated[str | None, Parameter(cookie=COOKIES["active_columns"])] = None,
    ) -> Template:
        # all_channels = await all_channels_cache()
        # all_file_formats = await all_file_formats_cache()
        active_columns_dict, disabled_columns_dict = get_actived_and_disabled_columns(active_columns_str)
        return Template(
            "telegram_browser/index.html",
            context={
                "active_columns": active_columns_dict,
                "disabled_columns": disabled_columns_dict,
            },
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
        active_columns_str: Annotated[str | None, Parameter(cookie=COOKIES["active_columns"])] = None,
    ) -> Template:
        logger.info(f"Search input: {data=}")
        active_columns_dict, disabled_columns_dict = get_actived_and_disabled_columns(active_columns_str)
        async with get_db() as db:
            results = await db.telegrammessage.find_many(
                # If "{}" then the filter will be ignored
                where={
                    "AND": [
                        # SEARCH TEXT
                        {"message_text": {"contains": data.search_text, "mode": "insensitive"}}
                        if data.search_text != ""
                        else {},
                        # CHANNEL NAME
                        {"channel": {"channel_username": data.channel_name}} if data.channel_name else {},
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
                        {"file_size_bytes": {"gte": data.file_size_min * 2**20}} if data.file_size_min != "" else {},
                        {"file_size_bytes": {"lte": data.file_size_max * 2**20}} if data.file_size_max != "" else {},
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
                # skip=0,  # TODO Pagination
            )
        results_as_dict: list[dict] = [
            {
                "message_link": f"https://t.me/{row.channel.channel_username.lower()}/{row.message_id}",
                "message_date": arrow.get(row.message_date).strftime("%Y-%m-%d %H:%M:%S"),
                "message_text": row.message_text if row.message_text is not None else "",
                "amount_of_reactions": row.amount_of_reactions,
                "amount_of_comments": row.amount_of_comments,
                "file_extension": row.file_extension if row.file_extension is not None else "-",
                "file_size_bytes": humanize.naturalsize(row.file_size_bytes, format="%d")
                if row.file_size_bytes is not None
                else "-",
                "file_duration_seconds": seconds_to_string(row.file_duration_seconds)
                if row.file_duration_seconds is not None
                else "-",
            }
            for row in results
        ]
        if len(results_as_dict) > 0:
            assert set(active_columns_dict) | set(disabled_columns_dict) == set(results_as_dict[0])
        return HTMXTemplate(
            template_name="telegram_browser/search_results.html",
            context={
                "table_headers": active_columns_dict,
                "results": [{col_key: row[col_key] for col_key in active_columns_dict} for row in results_as_dict],
            },
            # TODO Change url to represent search params
            # push_url="/asd",
        )

    @post("/queue-file")
    async def queue_download_file(
        self,
    ) -> None:
        "In database, set file to queued"

    @post("/delete-file")
    async def delete_file(
        self,
    ) -> None:
        "Delete file in database and in minio"

    @get("/view-file")
    async def view_file(
        self,
    ) -> None:
        """
        Allow the user to view the file in browser
        Return <video> element for videos, <audio> for audio, <img> for image
        """

    @get("/download-file")
    async def download_file(
        self,
    ) -> None:
        "Allow the user to download the file to file system"

    @post("/save-active-columns")
    async def save_active_columns(
        self,
        data: Annotated[dict, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Response[str]:
        "Allow the user to download the file to file system"

        column_order = data["columns-order"].split(";")
        return Response(
            content="",
            cookies=[
                Cookie(
                    key=COOKIES["active_columns"],
                    value=json.dumps(column_order),
                    path="/telegram-browser",
                    expires=10**10,
                ),
            ],
        )
