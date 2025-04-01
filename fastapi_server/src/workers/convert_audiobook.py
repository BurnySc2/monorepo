"""
TODO Keep service running, but spawn new workers if there are tasks to do, up to N workers
Requires proper observing if workers completed (success/fail), only then spawn new ones
"""

from __future__ import annotations

import asyncio
import io
import os
import re
import time
from contextlib import suppress

import arrow
from dotenv import load_dotenv
from loguru import logger
from minio import Minio, S3Error
from minio.helpers import _BUCKET_NAME_REGEX

from prisma import Prisma
from routes.audiobook.schema import (
    AudioSettings,
    get_chapter_combined_text,
)
from routes.audiobook.temp_generate_tts import generate_text_to_speech

load_dotenv()

# pyre-fixme[9]
MINIO_AUDIOBOOK_BUCKET: str = os.getenv("MINIO_AUDIOBOOK_BUCKET")
assert MINIO_AUDIOBOOK_BUCKET is not None
assert re.match(_BUCKET_NAME_REGEX, MINIO_AUDIOBOOK_BUCKET) is not None


# Increase this value to give converters more time to convert an audio
# Ideal value is slightly above 0.1
# TODO Export as env value
ESTIMATE_FACTOR = 0.3


async def convert_one() -> None:
    # Reset those that have failed to convert in time
    async with Prisma() as db:
        await db.audiobookchapter.update_many(
            where={
                "started_converting": {"lt": arrow.utcnow().datetime},
            },
            data={"started_converting": None},
        )

    # Abort if queue empty
    async with Prisma() as db:
        any_in_queue = await db.audiobookchapter.count(
            where={
                "minio_object_name": None,
                "queued": {"not": None},
                "started_converting": None,
            }
        )
    if any_in_queue == 0:
        return

    minio_client = Minio(
        # pyre-fixme[6]
        os.getenv("MINIO_INTERNAL_URL"),
        access_key=os.getenv("MINIO_ACCESS_TOKEN"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )
    # Create bucket if it doesn't exist
    with suppress(S3Error):
        minio_client.make_bucket(MINIO_AUDIOBOOK_BUCKET)

    # Get first book that is waiting to be converted
    async with Prisma() as db:
        chapter = await db.audiobookchapter.find_first(
            where={
                "minio_object_name": None,
                "queued": {"not": None},
                "started_converting": None,
            },
            order=[
                {"queued": "asc"},
                {"chapter_number": "asc"},
            ],
        )
        if chapter is None:
            return
        logger.info(f"Converting text to audio {chapter.id}...")

        # Mark chapter as "in_progress" converting
        # Datetime is the estimation when it should be done converting based on text length
        updated_count = await db.audiobookchapter.update_many(
            where={"id": chapter.id},
            data={
                "started_converting": arrow.utcnow()
                .shift(seconds=len(get_chapter_combined_text(chapter)) * ESTIMATE_FACTOR)
                .datetime
            },
        )
        assert updated_count == 1
    # Generate tts from the book
    audio_settings: AudioSettings = AudioSettings.model_validate(chapter.audio_settings)
    audio: io.BytesIO = await generate_text_to_speech(
        chapter.content,
        voice=audio_settings.voice_name,
        rate=audio_settings.voice_rate,
        volume=audio_settings.voice_volume,
        pitch=audio_settings.voice_pitch,
    )

    # Get data from db, user may have clicked "delete" button on book or chapter
    async with Prisma() as db:
        chapter2 = await db.audiobookchapter.find_first(where={"id": chapter.id})
        if chapter2 is None:
            # Book was deleted
            return
        if chapter.audio_settings != chapter2.audio_settings:
            # Audio was removed while conversion was in progress, and a new one was queued
            logger.info("Audio settings mismatch, skipping")
            return

        # Save result to database
        object_name = f"{chapter.id}_audio.mp3"
        minio_client.put_object(MINIO_AUDIOBOOK_BUCKET, object_name, audio, len(audio.getvalue()))
        logger.info("Saving result to database")
        await db.audiobookchapter.update_many(
            data={
                "started_converting": None,
                "minio_object_name": object_name,
            },
            where={"id": chapter.id},
        )
    logger.info(f"Done converting, saved to {object_name}")


async def keep_converting():
    while 1:
        t0 = time.time()
        await convert_one()
        diff = time.time() - t0
        if diff < 1:
            # Returned quickly, let docker compose choose when to restart
            return
        await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(keep_converting())
