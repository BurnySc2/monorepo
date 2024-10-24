from __future__ import annotations

import asyncio
import base64
import os
import re

from dotenv import load_dotenv
from minio import Minio
from pydantic import BaseModel

from prisma import models
from src.routes.caches import get_db

load_dotenv()
STAGE = os.getenv("STAGE", "local_dev")


minio_client = Minio(
    # pyre-fixme[6]
    os.getenv("MINIO_URL"),
    access_key=os.getenv("MINIO_ACCESS_TOKEN"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("STAGE") in {"prod"},
)


def normalize_title(title: str) -> str:
    normalized_title = title.title()
    # Replace any character that is not alphanumeric or underscore with a space
    normalized_title = re.sub(r"[^\w]", " ", normalized_title)
    # Replace two or more space with one space
    normalized_title = re.sub(r" +", " ", normalized_title)
    # Remove space from the start and end
    return normalized_title.strip()


def normalize_filename(text: str) -> str:
    return re.sub(" ", "_", normalize_title(text))


class AudioSettings(BaseModel):
    voice_name: str = ""
    voice_rate: int = 0
    voice_volume: int = 0
    voice_pitch: int = 0


def base64_encode_data(data: bytes) -> str:
    return base64.b64encode(data).decode("utf-8")


def base64_decode_data(data: str) -> bytes:
    return base64.b64decode(data)


def _minio_get_audio_of_chapter_sync(chapter: models.AudiobookChapter) -> bytes:
    # pyre-fixme[6]
    return minio_client.get_object(os.getenv("MINIO_AUDIOBOOK_BUCKET"), f"{chapter.id}_audio.mp3").data


async def minio_get_audio_of_chapter(chapter: models.AudiobookChapter) -> bytes:
    # Turn the minio API to be non-blocking by running it in a coroutine
    return await asyncio.to_thread(_minio_get_audio_of_chapter_sync, chapter)


def get_chapter_combined_text(chapter: models.AudiobookChapter) -> str:
    # Text still contains "\n" characters
    combined = " ".join(row for row in chapter.content)
    return re.sub(r"\s+", " ", combined)


async def get_chapter_position_in_queue(chapter: models.AudiobookChapter) -> int:
    if not chapter.queued or chapter.minio_object_name:
        return -1
    async with get_db() as db:
        return await db.audiobookchapter.count(
            # pyre-fixme[55]
            where={
                "queued": {"lte": chapter.queued},
                "started_converting": None,
                "minio_object_name": None,
            }
        )
