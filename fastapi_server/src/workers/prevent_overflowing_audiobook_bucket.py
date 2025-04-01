from __future__ import annotations

import asyncio
import os
import re
from contextlib import suppress

from loguru import logger
from minio import S3Error
from minio.helpers import _BUCKET_NAME_REGEX

from prisma import models
from routes.audiobook.schema import (
    minio_client,
)
from routes.caches import get_db

# pyre-fixme[9]
MINIO_AUDIOBOOK_BUCKET: str = os.getenv("MINIO_AUDIOBOOK_BUCKET")
assert MINIO_AUDIOBOOK_BUCKET is not None
assert re.match(_BUCKET_NAME_REGEX, MINIO_AUDIOBOOK_BUCKET) is not None


async def minio_get_bucket_size_in_mb(bucket_name: str) -> float:
    """Returns the total size used up by all object in the buckets in bytes."""

    def _minio_get_bucket_size_in_mb_sync(bucket_name: str) -> float:
        bucket_size_used_in_mb = 0
        for object in minio_client.list_objects(bucket_name, recursive=True):
            object_size_in_mb = object.size / 2**20
            bucket_size_used_in_mb += object_size_in_mb
        return bucket_size_used_in_mb

    return await asyncio.to_thread(_minio_get_bucket_size_in_mb_sync, bucket_name)


async def delete_book_return_bytes(book: models.AudiobookBook) -> int:
    """Delete a book and return the amount of bytes freed."""

    def delete_minio_objects(bucket_name: str, object_names: list[str]) -> None:
        # minio_client.remove_objects does not work
        for minio_object_name in object_names:
            minio_client.remove_object(bucket_name, minio_object_name)

    total_size_freed = 0
    chapter_objects_to_remove: list[str] = []
    chapter: models.AudiobookChapter
    # pyre-fixme[16]
    for chapter in book.AudiobookChapter:
        if chapter.minio_object_name is None:
            continue
        chapter_object = await asyncio.to_thread(
            minio_client.stat_object,
            MINIO_AUDIOBOOK_BUCKET,
            chapter.minio_object_name,
        )
        chapter_objects_to_remove.append(chapter.minio_object_name)
        if chapter_object.size is None:
            continue
        total_size_freed += chapter_object.size
    await asyncio.to_thread(
        delete_minio_objects,
        MINIO_AUDIOBOOK_BUCKET,
        chapter_objects_to_remove,
    )
    async with get_db() as db:
        await db.audiobookbook.delete(where={"id": book.id})
    return total_size_freed


async def prevent_overflowing_audiobook_bucket() -> None:
    """Keep minio bucket size below a maximum by removing oldest uploaded books and minio data."""
    # pyre-fixme[9]
    minio_audiobook_max_size_mb_str: str = os.getenv("MINIO_AUDIOBOOK_MAX_SIZE_MB")
    minio_audiobook_max_size_mb: int = int(minio_audiobook_max_size_mb_str)
    while 1:
        with suppress(S3Error):
            await asyncio.to_thread(minio_client.make_bucket, MINIO_AUDIOBOOK_BUCKET)
        minio_audiobooks_size_used_mb = await minio_get_bucket_size_in_mb(MINIO_AUDIOBOOK_BUCKET)
        while minio_audiobooks_size_used_mb > minio_audiobook_max_size_mb:
            # Delete book and minio data
            async with get_db() as db:
                oldest_book = await db.audiobookbook.find_first(
                    where={},
                    include={"AudiobookChapter": True},
                    order=[{"upload_date": "asc"}],
                )
            if oldest_book is None:
                break
            logger.info(f"Deleting book to free up space: {oldest_book.id}")
            _size_freed: int = await delete_book_return_bytes(oldest_book)
            minio_audiobooks_size_used_mb = await minio_get_bucket_size_in_mb(MINIO_AUDIOBOOK_BUCKET)

        # Repeat every hour
        await asyncio.sleep(3600)
