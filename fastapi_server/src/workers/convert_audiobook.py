from __future__ import annotations

import asyncio
import io
import os
import re
from typing import cast

import arrow
from dotenv import load_dotenv
from loguru import logger

from components.tts_generate import generate_audio
from s3_helper import RUSTFS_AUDIOBOOK_BUCKET, get_s3_client, object_upload
from schemas.audiobook import AudioSettings
from schemas.audiobook.db_models import AudiobookChapter

load_dotenv()


# Increase this value to give converters more time to convert an audio
# Ideal value is slightly above 0.3
ESTIMATE_FACTOR = float(os.getenv("AUDIOBOOK_CONVERT_ESTIMATE_FACTOR", "0.3"))

# Maximum number of concurrent chapter conversions
MAX_CONCURRENT_CONVERSIONS = int(os.getenv("AUDIOBOOK_MAX_CONCURRENT_CONVERSIONS", "1"))


def get_chapter_combined_text(text: str) -> str:
    combined = " ".join(row for row in text)
    return re.sub(r"\s+", " ", combined)


# TODO Investigate why the following is better:
# def get_chapter_combined_text(text: str) -> str:
#     lines = text.splitlines()
#     combined = " ".join(row.strip() for row in lines if row.strip())
#     return re.sub(r"\s+", " ", combined).strip()


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
        # Generate s3 object name
        # pyrefly: ignore
        self.minio_object_name = f"{self.chapter.id}_audio.mp3"
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        chapter_id = self.chapter.id
        try:
            if exc_type is None:
                # Conversion succeeded - clear converting flag
                await AudiobookChapter.update(
                    {
                        AudiobookChapter.started_converting: None,
                        AudiobookChapter.minio_object_name: self.minio_object_name,
                    }
                ).where(AudiobookChapter.id == chapter_id)
            else:
                # Conversion failed - reset converting flag
                await AudiobookChapter.update(
                    {
                        AudiobookChapter.started_converting: None,
                    }
                ).where(AudiobookChapter.id == chapter_id)
                logger.error(f"Conversion failed: {exc_val}")
        except Exception as e:
            logger.exception(f"Error in context manager cleanup: {e}")
            raise


async def check_queued_chapters() -> bool:
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
        return False

    # Check active conversions count
    # pyrefly: ignore
    active_conversions = cast(
        int, await AudiobookChapter.count().where(arrow.utcnow().naive < AudiobookChapter.started_converting)
    )
    if MAX_CONCURRENT_CONVERSIONS <= active_conversions:
        return False

    count_more_conversion_possible = MAX_CONCURRENT_CONVERSIONS - active_conversions
    chapters = await query.limit(count_more_conversion_possible)
    for chapter in chapters:
        # Launch convert_one in a new asyncio task
        asyncio.create_task(convert_one(chapter))
    return True


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
        audio_settings: AudioSettings = AudioSettings.model_validate_json(chapter.audio_settings)

        result = await generate_audio(
            audio_settings.engine_name,
            audio_settings.voice_name,
            chapter.content,
        )
        audio = io.BytesIO(result[0])

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
            async with get_s3_client() as s3:
                await object_upload(
                    s3, RUSTFS_AUDIOBOOK_BUCKET, context.minio_object_name, audio
                )  # pyrefly: ignore[bad-argument-type]
            logger.debug(f"Successfully saved audio to s3 storage: {context.minio_object_name}")
        except Exception as e:
            logger.exception(f"Failed to save audio to s3 storage: {e}")
            raise

    logger.info(f"Done converting, saved to {context.minio_object_name}")


async def keep_converting():
    """Main worker loop that continuously checks for and processes queued chapters."""
    logger.info("Starting audiobook conversion worker")
    while True:
        try:
            converted_one = await check_queued_chapters()
            if not converted_one:
                await asyncio.sleep(30)
        except Exception as e:  # noqa: BLE001
            logger.exception(f"Error in conversion loop: {e}")
            await asyncio.sleep(5)  # Brief pause before retrying


if __name__ == "__main__":
    asyncio.run(keep_converting())
