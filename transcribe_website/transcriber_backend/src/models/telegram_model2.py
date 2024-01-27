"""
Database models for postgres
"""
from __future__ import annotations

import datetime
import enum
from dataclasses import dataclass

from pony import orm  # pyre-fixme[21]

from src.models import db
from src.secrets_loader import SECRETS as SECRETS_FULL

SECRETS = SECRETS_FULL.TelegramDownloader


class Status(enum.Enum):
    """Possible status of a message in the db."""

    UNKNOWN = 0
    # Planned to download
    QUEUED = 1
    # Ignored because of current filters
    FILTERED = 2
    # Downloading
    DOWNLOADING = 3
    # Done downloading
    DUPLICATE = 9
    COMPLETED = 6
    # Errors
    MISSING_FILE_NAME = 4
    MISSING_FILE_TYPE = 10
    NO_MEDIA = 5
    ERROR_DOWNLOADING = 7
    ERROR_EXTRACTING_AUDIO = 8
    ERROR_CHANNEL_INACCESSIBLE = 9


# pyre-fixme[11]
class TelegramChannel(db.Entity):
    _table_ = "telegram_channels"  # Table name
    id = orm.PrimaryKey(int, auto=True)
    channel_id = orm.Required(str)
    # Check if the oldest message has been reached
    done_parsing = orm.Required(bool, default=False)
    # Check for new messages
    last_parsed = orm.Required(datetime.datetime, default=datetime.datetime.utcnow)


@dataclass
class TelegramMessage2:
    id: int
    channel_id: str
    message_id: int
    message_date: datetime.datetime
    link: str
    download_status: str
    # Prevent duplicate
    downloaded_file_path: str | None  # Relative file path to download dir
    # File meta info
    media_type: str | None
    # Prevent duplicate
    file_unique_id: str | None
    file_size_bytes: int | None  # needs to be 64bit
    file_duration_seconds: int | None
    file_height: int | None
    file_width: int | None
    issued_by: str | None
    # TODO Add another columun for mp3 file path and mp3 file size?
    extracted_mp3_size_bytes: int  # 64 bit
    linked_transcription: int
