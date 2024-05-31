from __future__ import annotations

import asyncio
import datetime
import io
import os
from collections import OrderedDict

from dotenv import load_dotenv
from loguru import logger
from minio import Minio

from routes.audiobook.schema import (
    AudioSettings,
    Chapter,
    chapter_table,
    db,
)
from routes.audiobook.temp_generate_tts import generate_text_to_speech

load_dotenv()

ESTIMATE_FACTOR = 0.1


async def convert_one():
    datetime_now = datetime.datetime.now(datetime.timezone.utc)

    # Reset those that have failed to convert in time
    entries = [
        {
            "id": c["id"],
            "converting": None,
        }
        for c in chapter_table.find(converting={"<": datetime_now})
    ]
    if len(entries) > 0:
        chapter_table.update_many(entries, keys=["id"])

    # Abort if queue empty
    any_in_queue = chapter_table.count(minio_object_name=None, queued={"!=": None}, converting=None)
    if any_in_queue == 0:
        return

    client = Minio(
        os.getenv("MINIO_URL"),
        os.getenv("MINIO_ACCESS_TOKEN"),
        os.getenv("MINIO_SECRET_KEY"),
    )

    # Get first book that is waiting to be converted
    with db:
        chapter_entry: OrderedDict = chapter_table.find_one(
            minio_object_name=None,
            queued={"!=": None},
            converting=None,
            order_by=["queued", "chapter_number"],
        )
        chapter: Chapter = Chapter.model_validate(chapter_entry)
        logger.info(f"Converting text to audio {chapter.id}...")

        # Mark chapter as "in_progress" converting
        # Datetime is the estimation when it should be done converting based on text length
        chapter.converting = datetime_now + datetime.timedelta(seconds=len(chapter.combined_text) * ESTIMATE_FACTOR)
        chapter_table.update(
            chapter.model_dump(),
            keys=["id"],
        )
    # Generate tts from the book
    audio_settings: AudioSettings = chapter.audio_settings
    audio: io.BytesIO = await generate_text_to_speech(
        chapter.combined_text,
        voice=audio_settings.voice_name,
        rate=audio_settings.voice_rate,
        volume=audio_settings.voice_volume,
        pitch=audio_settings.voice_pitch,
    )

    # Get data from db, user may have clicked "delete" button on book or chapter
    chapter_entry2: OrderedDict = chapter_table.find_one(id=chapter.id)
    if chapter_entry2 is None:
        # Book was deleted
        return
    chapter2: Chapter = Chapter.model_validate(chapter_entry2)
    if chapter.audio_settings != chapter2.audio_settings:
        # Audio was removed while conversion was in progress
        logger.info("Audio settings mismatch, skipping")
        return

    # Save result to database
    with db:
        object_name = f"{chapter.id}_audio.mp3"
        client.put_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{chapter.id}_audio.mp3", audio, len(audio.getvalue()))
        chapter.converting = None
        chapter.minio_object_name = object_name
        logger.info("Saving result to database")
        chapter_table.update(
            chapter.model_dump(),
            keys=["id"],
        )
    logger.info("Done converting")


if __name__ == "__main__":
    asyncio.run(convert_one())
    # import time
    # while 1:
    #     asyncio.run(convert_one())
    #     time.sleep(10)
