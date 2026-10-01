from __future__ import annotations

import asyncio
from types import TracebackType
from typing import cast

import arrow
import httpx
from botocore.exceptions import ClientError
from loguru import logger
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential

from components.audiobook.epub_reader import combine_text
from components.tts_generate import generate_audio
from s3_helper import (
    RUSTFS_AUDIOBOOK_BUCKET,
    ensure_bucket,
    get_s3_client,
    object_upload,
)
from schemas.audiobook import AudioSettings
from schemas.audiobook.db_models import AudiobookChapter
from schemas.tts.engine import TTSEngine
from settings import settings

# Increase this value to give converters more time to convert an audio
# Ideal value is slightly above 0.3
ESTIMATE_FACTOR = settings.audiobook_convert_estimate_factor

# Maximum number of concurrent chapter conversions
MAX_CONCURRENT_CONVERSIONS = settings.audiobook_max_concurrent_conversions

_background_tasks: set[asyncio.Task[None]] = set()


def _is_retryable_audio_error(exc: BaseException) -> bool:
    """Retry transient network/S3 errors only (no retry for ValueError/AssertionError/RuntimeError)."""
    if isinstance(exc, (httpx.HTTPError, TimeoutError)):
        return True
    if isinstance(exc, ClientError):
        response = getattr(exc, "response", None)
        error = response.get("Error", {}) if isinstance(response, dict) else {}
        code = str(error.get("Code", ""))
        if code in ("404", "NoSuchKey", "NoSuchBucket", "NotFound"):
            return False
        return code == "" or code.startswith("5") or "Throttle" in code or "TooMany" in code or "Timeout" in code
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_is_retryable_audio_error),
    reraise=True,
)
async def _generate_audio_with_retry(engine_name: str, voice_name: str, content: str) -> tuple[bytes, float]:
    return await generate_audio(cast(TTSEngine, engine_name), voice_name, content)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception(_is_retryable_audio_error),
    reraise=True,
)
async def _upload_audio_with_retry(bucket: str, key: str, data: bytes) -> None:
    async with get_s3_client() as s3:
        await object_upload(s3, bucket, key, data)


def _on_background_task_done(task: asyncio.Task[None]) -> None:
    """Drop finished tasks and log failures so they are never silent."""
    _background_tasks.discard(task)
    try:
        exc = task.exception()
    except asyncio.CancelledError:
        return
    if exc is not None:
        logger.exception(f"Background audiobook conversion failed: {exc}")


def get_chapter_combined_text(text: str | list[str]) -> str:
    """Backward-compatible shim delegating to :func:`epub_reader.combine_text`.

    Historically took a raw ``content`` string; now also accepts a list of
    lines. Strings are split into lines before delegating.
    """
    if isinstance(text, str):
        return combine_text(text.splitlines())
    return combine_text(text)


class AudiobookConversionContext:
    def __init__(self, chapter: AudiobookChapter) -> None:
        self.chapter: AudiobookChapter = chapter
        self.minio_object_name: str | None = None

    async def __aenter__(self) -> AudiobookConversionContext:
        # Lock the chapter for conversion
        self.chapter.started_converting = (
            arrow.utcnow().shift(seconds=len(get_chapter_combined_text(self.chapter.content)) * ESTIMATE_FACTOR).naive
        )
        await self.chapter.save()
        # Generate s3 object name
        # pyrefly: ignore[missing-attribute]
        self.minio_object_name = f"{self.chapter.id}_audio.mp3"
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        chapter_id = self.chapter.id  # pyrefly: ignore[missing-attribute]
        try:
            if exc_type is None:
                # Conversion succeeded - clear converting flag
                await AudiobookChapter.update(
                    {
                        AudiobookChapter.started_converting: None,
                        AudiobookChapter.minio_object_name: self.minio_object_name,
                    }
                ).where(AudiobookChapter.id == chapter_id)  # pyrefly: ignore[missing-attribute]
            else:
                # Conversion failed - reset converting flag
                await AudiobookChapter.update(
                    {
                        AudiobookChapter.started_converting: None,
                    }
                ).where(AudiobookChapter.id == chapter_id)  # pyrefly: ignore[missing-attribute]
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
        AudiobookChapter.objects()
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
    active_conversions = cast(
        int, await AudiobookChapter.count().where(arrow.utcnow().naive < AudiobookChapter.started_converting)
    )
    if MAX_CONCURRENT_CONVERSIONS <= active_conversions:
        return False

    count_more_conversion_possible = MAX_CONCURRENT_CONVERSIONS - active_conversions
    chapters = await query.limit(count_more_conversion_possible)
    for chapter in chapters:
        task_name = f"audiobook-convert-{getattr(chapter, 'id', 'unknown')}-{getattr(chapter, 'chapter_number', '?')}"
        task = asyncio.create_task(convert_one(chapter), name=task_name)
        _background_tasks.add(task)
        task.add_done_callback(_on_background_task_done)
    return True


async def convert_one(chapter: AudiobookChapter) -> None:
    """Convert a single audiobook chapter to audio using text-to-speech.

    Args:
        chapter: The chapter to convert containing text content and audio settings
    """
    logger.info(f"Starting conversion for chapter {chapter.chapter_number} (book: {chapter.book})")
    logger.debug(f"Audio settings: {chapter.audio_settings}")

    async with AudiobookConversionContext(chapter) as context:
        # Generate tts from the book
        audio_settings: AudioSettings = AudioSettings.model_validate_json(chapter.audio_settings)

        result = await _generate_audio_with_retry(
            audio_settings.engine_name,
            audio_settings.voice_name,
            chapter.content,
        )
        audio = result[0]

        # Get data from db, user may have clicked "delete" button on book or chapter
        # pyrefly: ignore[missing-attribute]
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
            assert context.minio_object_name is not None, "Missing S3 object name"
            await _upload_audio_with_retry(RUSTFS_AUDIOBOOK_BUCKET, context.minio_object_name, audio)
            logger.debug(f"Successfully saved audio to s3 storage: {context.minio_object_name}")
        except Exception as e:
            logger.exception(f"Failed to save audio to s3 storage: {e}")
            raise

    logger.info(f"Done converting, saved to {context.minio_object_name}")


async def keep_converting():
    """Main worker loop that continuously checks for and processes queued chapters."""
    logger.info("Starting audiobook conversion worker")
    await ensure_bucket(RUSTFS_AUDIOBOOK_BUCKET, settings.rustfs_audiobook_bucket_expiration_days, raise_on_error=False)
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
