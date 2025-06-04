"""
TODO Keep service running, but spawn new workers if there are tasks to do, up to N workers
Requires proper observing if workers completed (success/fail), only then spawn new ones
"""

from __future__ import annotations

import asyncio
import io
import os
import time
from contextlib import suppress

import arrow
from dotenv import load_dotenv
from loguru import logger
from minio import Minio, S3Error

from models.audiobook import AudiobookChapter
from routes.audiobook.my_minio_client import (
    MINIO_AUDIOBOOK_BUCKET,
    AudioSettings,
    get_chapter_combined_text,
)
from routes.audiobook.temp_generate_tts import generate_text_to_speech

load_dotenv()


# Increase this value to give converters more time to convert an audio
# Ideal value is slightly above 0.1
# TODO Export as env value
ESTIMATE_FACTOR = float(os.getenv("AUDIOBOOK_CONVERT_ESTIMATE_FACTOR"))


"""
TODO Refactor:
Run this only once in parallel
Instead, this script will create async workers (8, 16?)

Use with async with contextmanager
- on enter: set chapter to converting
- on exit (finally): set no longer to converting

workers will end themselves if done (success or error)

fetcher:
- fetch jobs every 10s
- assign jobs to workers
- create workers (up to LIMIT)
"""


class AudiobookConversionContext:
    def __init__(self, chapter: AudiobookChapter):
        self.chapter = chapter
        self.minio_object_name = None

    async def __aenter__(self):
        # Lock the chapter for conversion
        self.chapter.started_converting = (
            arrow.utcnow()
            .shift(seconds=len(get_chapter_combined_text(self.chapter.content)) * ESTIMATE_FACTOR)
            .datetime
        )
        await self.chapter.save()
        # Generate MinIO object name
        self.minio_object_name = f"{self.chapter.id}_audio.mp3"
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is None:
                # Conversion succeeded - clear converting flag
                self.chapter.started_converting = None
                await self.chapter.save()
            else:
                # Conversion failed - reset converting flag
                self.chapter.started_converting = None
                await self.chapter.save()
                logger.error(f"Conversion failed: {exc_val}")
        except Exception as e:
            logger.error(f"Error in context manager cleanup: {e}")
            raise


async def convert_one() -> None:
    # Reset those that have failed to convert in time
    await AudiobookChapter.update({AudiobookChapter.started_converting: None}).where(
        AudiobookChapter.started_converting <= arrow.utcnow().datetime
    )

    # Abort if queue empty
    # pyrefly: ignore
    count_in_queue = await AudiobookChapter.count().where(
        (AudiobookChapter.minio_object_name != None)  # noqa: E711
        & (AudiobookChapter.queued != None)  # noqa: E711
        & (AudiobookChapter.started_converting == None)  # noqa: E711
    )
    if count_in_queue == 0:
        return

    minio_client = Minio(
        # pyre-fixme[6]
        os.getenv("MINIO_URL"),
        access_key=os.getenv("MINIO_ACCESS_TOKEN"),
        secret_key=os.getenv("MINIO_SECRET_KEY"),
        secure=os.getenv("MINIO_SECURE") == "TRUE",
    )
    # Create bucket if it doesn't exist
    with suppress(S3Error):
        minio_client.make_bucket(MINIO_AUDIOBOOK_BUCKET)

    # Get first book that is waiting to be converted
    chapter = (
        # pyrefly: ignore
        await AudiobookChapter.objects()
        .where(
            (AudiobookChapter.minio_object_name != None)  # noqa: E711
            & (AudiobookChapter.queued != None)  # noqa: E711
            & (AudiobookChapter.started_converting == None)  # noqa: E711
        )
        .order_by(AudiobookChapter.queued, ascending=True)
        .order_by(AudiobookChapter.chapter_number, ascending=True)
        .first()
    )
    if chapter is None:
        return
    logger.info(f"Converting text to audio {chapter.id}...")

    async with AudiobookConversionContext(chapter) as context:
        # Generate tts from the book
        audio_settings: AudioSettings = AudioSettings.model_validate_json(chapter.audio_settings)
        audio: io.BytesIO = await generate_text_to_speech(
            chapter.content,
            voice=audio_settings.voice_name,
            rate=audio_settings.voice_rate,
            volume=audio_settings.voice_volume,
            pitch=audio_settings.voice_pitch,
        )

        # Get data from db, user may have clicked "delete" button on book or chapter
        # pyrefly: ignore
        chapter2 = await AudiobookChapter.objects().where(AudiobookChapter.id == chapter.id).first()
        if chapter2 is None:
            # Book was deleted
            return
        if chapter.audio_settings != chapter2.audio_settings:
            # Audio was removed while conversion was in progress, and a new one was queued
            logger.info("Audio settings mismatch, skipping")
            return

        # Save result to MinIO
        minio_client.put_object(MINIO_AUDIOBOOK_BUCKET, context.minio_object_name, audio, len(audio.getvalue()))

        # Save result to database
        chapter.minio_object_name = context.minio_object_name
        await chapter.save()

        logger.info(f"Done converting, saved to {context.minio_object_name}")


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
