from __future__ import annotations

import asyncio
import base64
import os
import re
from minio.helpers import _BUCKET_NAME_REGEX

from dotenv import load_dotenv
from minio import Minio, S3Error
from pydantic import BaseModel

from models.audiobook import AudiobookBook, AudiobookChapter

load_dotenv()

# pyre-fixme[9]
MINIO_AUDIOBOOK_BUCKET: str = os.getenv("MINIO_AUDIOBOOK_BUCKET")
assert MINIO_AUDIOBOOK_BUCKET is not None
assert re.match(_BUCKET_NAME_REGEX, MINIO_AUDIOBOOK_BUCKET) is not None

minio_client = Minio(
    # pyre-fixme[6]
    os.getenv("MINIO_URL"),
    access_key=os.getenv("MINIO_ACCESS_TOKEN"),
    secret_key=os.getenv("MINIO_SECRET_KEY"),
    secure=os.getenv("MINIO_SECURE") == "TRUE",
)


async def minio_check_if_object_exists(bucket_name: str, object_name: str) -> bool:
    try:
        # Attempt to get object metadata
        minio_client.stat_object(bucket_name, object_name)
        return True
    except S3Error as err:
        # If object doesn't exist, MinIO returns a "NoSuchKey" error
        if err.code == "NoSuchKey":
            return False
        # Raise other errors (like connection issues)
        raise


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


# def base64_encode_data(data: bytes) -> str:
#     return base64.b64encode(data).decode("utf-8")


# def base64_decode_data(data: str) -> bytes:
#     return base64.b64decode(data)


def get_chapter_combined_text(text: str) -> str:
    # Text still contains "\n" characters
    combined = " ".join(row for row in text)
    return re.sub(r"\s+", " ", combined)


def delete_minio_objects(bucket_name: str, object_names: list[str]) -> None:
    # minio_client.remove_objects does not work
    for minio_object_name in object_names:
        minio_client.remove_object(bucket_name, minio_object_name)


async def hard_delete_book(book_id: int) -> None:
    minio_objects = (
        await AudiobookChapter.select(AudiobookChapter.minio_object_name)
        .where(AudiobookChapter.book == book_id)
        .where(AudiobookChapter.minio_object_name != None)  # noqa: E711
    )

    # TODO Wrap in transaction
    # Delete minio objects
    names = [i["minio_object_name"] for i in minio_objects]
    await asyncio.to_thread(delete_minio_objects, MINIO_AUDIOBOOK_BUCKET, names)

    # Delete chapters
    await AudiobookChapter.delete().where(AudiobookChapter.book == book_id)

    # Delete book
    await AudiobookBook.delete().where(AudiobookBook.id == book_id)
