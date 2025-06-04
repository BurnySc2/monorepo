from __future__ import annotations

import asyncio
import os
from contextlib import suppress

from loguru import logger
from minio import S3Error

from models.audiobook import AudiobookBook
from routes.audiobook.my_minio_client import (
    MINIO_AUDIOBOOK_BUCKET,
    hard_delete_book,
    minio_client,
)


async def minio_get_bucket_size_in_mb(bucket_name: str) -> float:
    """Returns the total size used up by all object in the buckets in bytes."""

    def _minio_get_bucket_size_in_mb_sync(bucket_name: str) -> float:
        bucket_size_used_in_mb = 0
        for object in minio_client.list_objects(bucket_name, recursive=True):
            object_size_in_mb = object.size / 2**20
            bucket_size_used_in_mb += object_size_in_mb
        return bucket_size_used_in_mb

    return await asyncio.to_thread(_minio_get_bucket_size_in_mb_sync, bucket_name)


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
            oldest_book = await AudiobookBook.objects().order_by(AudiobookBook.upload_date).first()
            if oldest_book is None:
                break
            logger.info(f"Deleting book to free up space: {oldest_book.id}")
            await hard_delete_book(oldest_book.id)
            minio_audiobooks_size_used_mb = await minio_get_bucket_size_in_mb(MINIO_AUDIOBOOK_BUCKET)

        # Repeat every hour
        await asyncio.sleep(3600)
