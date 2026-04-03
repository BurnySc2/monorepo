from __future__ import annotations

import asyncio
import io
import os

import arrow
from dotenv import load_dotenv
from loguru import logger

from minio_helper import GARAGE_AUDIOBOOK_BUCKET, get_s3_client, object_upload
from models.audiobook import AudiobookChapter
from components.audiobook.generate_tts import generate_text_to_speech
from components.audiobook.models import AudioSettingsBaseModel, get_chapter_combined_text

load_dotenv()


# Increase this value to give converters more time to convert an audio
# Ideal value is slightly above 0.3
ESTIMATE_FACTOR = float(os.getenv("AUDIOBOOK_CONVERT_ESTIMATE_FACTOR", "0.3"))

# Maximum number of concurrent chapter conversions
MAX_CONCURRENT_CONVERSIONS = int(os.getenv("AUDIOBOOK_MAX_CONCURRENT_CONVERSIONS", "1"))


class AudiobookConversionContext:
    def __init__(self, chapter: AudiobookChapter):
        self.chapter = chapter
        self.minio_object_name = None

    async def __aenter__(self):
        # Lock the chapter for conversion
        self.chapter.started_converting = (
            arrow.utcnow().shift(seconds=len(get_chapter_combined_text(self.chapter.content)) * ESTIMATE_FACTOR).naive
        )
        await self.chapter.save()
        # Generate MinIO object name
        # pyrefly: ignore
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


async def check_queued_chapters() -> None:
    # Reset those that have failed to convert in time
    await AudiobookChapter.update({AudiobookChapter.started_converting: None}).where(
        AudiobookChapter.started_converting <= arrow.utcnow().naive
    )

    # Get first book that is waiting to be converted
    query = (
        # pyrefly: ignore
        AudiobookChapter.objects()
        # pyrefly: ignore
        .where(
            (AudiobookChapter.minio_object_name == None)  # noqa: E711
            & (AudiobookChapter.queued != None)  # noqa: E711
            & (AudiobookChapter.started_converting == None)  # noqa: E711
        )
        .order_by(AudiobookChapter.queued, ascending=True)
        .order_by(AudiobookChapter.chapter_number, ascending=True)
    )
    first_chapter = await query.first()
    if first_chapter is None:
        return

    # Check active conversions count
    # pyrefly: ignore
    active_conversions: int = await AudiobookChapter.count().where(
        arrow.utcnow().naive < AudiobookChapter.started_converting
    )
    if MAX_CONCURRENT_CONVERSIONS <= active_conversions:
        return

    count_more_conversion_possible = MAX_CONCURRENT_CONVERSIONS - active_conversions
    chapters = await query.limit(count_more_conversion_possible)
    for chapter in chapters:
        # Launch convert_one in a new asyncio task
        asyncio.create_task(convert_one(chapter))


async def convert_one(chapter: AudiobookChapter) -> None:
    """Convert a single audiobook chapter to audio using text-to-speech.

    Args:
        chapter: The chapter to convert containing text content and audio settings
    """
    # pyrefly: ignore
    logger.info(f"Starting conversion for chapter {chapter.chapter_number} (book: {chapter.book})")
    logger.debug(f"Audio settings: {chapter.audio_settings}")

    async with AudiobookConversionContext(chapter) as context:
        # Generate tts from the book
        audio_settings: AudioSettingsBaseModel = AudioSettingsBaseModel.model_validate_json(chapter.audio_settings)
        audio: io.BytesIO = await generate_text_to_speech(
            chapter.content,
            voice=audio_settings.voice,
            rate=audio_settings.rate,
            volume=audio_settings.volume,
            pitch=audio_settings.pitch,
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
        try:
            # pyrefly: ignore
            async with get_s3_client() as s3:
                await object_upload(s3, GARAGE_AUDIOBOOK_BUCKET, context.minio_object_name, audio)
            logger.debug(f"Successfully saved audio to MinIO: {context.minio_object_name}")
        except Exception as e:
            logger.error(f"Failed to save audio to MinIO: {e}")
            raise

        # Save result to database after exiting context
        context.chapter.minio_object_name = context.minio_object_name

    logger.info(f"Done converting, saved to {context.minio_object_name}")


async def keep_converting():
    """Main worker loop that continuously checks for and processes queued chapters."""
    logger.info("Starting audiobook conversion worker")
    while True:
        try:
            await check_queued_chapters()
            await asyncio.sleep(30)
        except Exception as e:  # noqa: BLE001
            logger.error(f"Error in conversion loop: {e}")
            await asyncio.sleep(5)  # Brief pause before retrying


if __name__ == "__main__":
    asyncio.run(keep_converting())
