from __future__ import annotations

import datetime
import enum
from pathlib import Path

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


# pyre-fixme[11]
class TelegramChannel(db.Entity):
    _table_ = "telegram_channels"  # Table name
    id = orm.PrimaryKey(int, auto=True)
    channel_id = orm.Required(str)
    done_parsing = orm.Required(bool, default=False)


class TelegramMessage(db.Entity):
    # TODO Filter duplicate message, maybe with combination of "size_bytes" and "duration_seconds" has to be unique
    _table_ = "telegram_messages_to_download"  # Table name
    id = orm.PrimaryKey(int, auto=True)
    channel_id = orm.Required(str)
    message_id = orm.Required(int)
    message_date = orm.Required(datetime.datetime)
    link = orm.Required(str)
    download_status = orm.Required(str)
    # Prevent duplicate
    downloaded_file_path = orm.Optional(str, unique=True, nullable=True)  # Relative file path to download dir
    # File meta info
    media_type = orm.Optional(str)
    # Prevent duplicate
    file_unique_id = orm.Optional(str)
    file_size_bytes = orm.Optional(int, size=64)
    file_duration_seconds = orm.Optional(int)
    file_height = orm.Optional(int)
    file_width = orm.Optional(int)
    issued_by = orm.Optional(str)
    # TODO Add another columun for mp3 file path and mp3 file size?
    extracted_mp3_size_bytes = orm.Optional(int, size=64, nullable=True)
    linked_transcription = orm.Optional("TranscriptionJob")

    @property
    def temp_download_path(self) -> Path:
        return SECRETS.output_folder_path / "downloading" / f"{self.file_unique_id}.temp"

    @property
    def media_ending(self) -> str:
        if self.media_type == "Video":
            return ".mp4"
        if self.media_type == "Audio":
            return ".mp3"
        if self.media_type == "Photo":
            return ".jpg"
        raise ValueError(f"Unknown media type: {self.media_type}")

    @property
    def output_file_path(self) -> Path:
        if self.media_type == "Video" and SECRETS.extract_audio_from_videos:
            return SECRETS.output_folder_path / self.channel_id / "extracted_audio" / f"{self.file_unique_id}.mp3"
        return (
            SECRETS.output_folder_path / self.channel_id / self.media_type / f"{self.file_unique_id}{self.media_ending}"
        )

    @property
    def download_completed(self) -> bool:
        return self.output_file_path.is_file()

    @property
    def relative_path(self) -> str:
        # Path that needs to be stored in DB without the root download folder,
        # so that the root download folder may be moved
        return str(self.output_file_path.relative_to(SECRETS.output_folder_path))

    @staticmethod
    def get_one_queued() -> TelegramMessage | None:
        """Used in getting a single queued message for the download-worker."""
        with orm.db_session():
            messages: list[TelegramMessage] = list(
                orm.select(
                    # pyre-fixme[16]
                    m for m in TelegramMessage if m.download_status == Status.QUEUED.name
                ).order_by(
                    TelegramMessage.channel_id,
                    TelegramMessage.file_size_bytes,
                ).limit(1)
            )
            if len(messages) > 0:
                return messages[0]

    @staticmethod
    def get_n_queued_by_channel(channel_id: str, limit: int = 200) -> list[int]:
        """Get a bunch of queued messages of a channel to batch-update their file ids."""
        with orm.db_session():
            messages: list[TelegramMessage] = orm.select(
                # pyre-fixme[16]
                m for m in TelegramMessage if m.download_status == Status.QUEUED.name and m.channel_id == channel_id
            ).order_by(
                TelegramMessage.file_size_bytes,
            ).limit(limit)
            return [m.message_id for m in messages]

    @staticmethod
    def get_oldest_message_id(channel_id: str) -> int:
        """Used in finding the oldest parsed message_id of a channel. Returns 0 if channel has not been parsed yet."""
        with orm.db_session():
            # pyre-fixme[16]
            messages = orm.select(m for m in TelegramMessage if m.channel_id == channel_id).order_by(
                TelegramMessage.message_id,
            ).limit(1)
            if len(messages) == 0:
                return 0
            return list(messages)[0].message_id

    @staticmethod
    def get_count() -> tuple[int, int, int, int]:
        """Returns a tuple of how many downloads are complete and how many total there are. 
        Also how many bytes are done downloading and how many there are in total."""
        done_status = [Status.DUPLICATE.name, Status.COMPLETED.name]
        total_count_status = [
            Status.QUEUED.name,
            Status.DOWNLOADING.name,
            Status.DUPLICATE.name,
            Status.COMPLETED.name,
        ]
        with orm.db_session():
            done_count = orm.count(
                # pyre-fixme[16]
                m for m in TelegramMessage if m.download_status in done_status
            )
            total_count = orm.count(m for m in TelegramMessage if m.download_status in total_count_status)
            done_bytes = orm.sum(m.file_size_bytes for m in TelegramMessage if m.download_status in done_status)
            total_bytes = orm.sum(m.file_size_bytes for m in TelegramMessage if m.download_status in total_count_status)
            return done_count, total_count, done_bytes, total_bytes

    @staticmethod
    def get_count_without_transcription() -> tuple[int, int, int, int]:
        """Returns a tuple of how many uploads are complete and how many total there are. 
        Also how many bytes are done uploading and how many there are in total."""
        with orm.db_session():
            done_count = orm.count(
                # pyre-fixme[16]
                m for m in TelegramMessage if m.linked_transcription is not None
            )
            total_count = orm.count(
                m for m in TelegramMessage
                if (m.downloaded_file_path is not None and m.download_status == Status.COMPLETED.name)
            )
            done_bytes = orm.sum(
                m.extracted_mp3_size_bytes for m in TelegramMessage if m.linked_transcription is not None
            )
            total_bytes = orm.sum(
                m.extracted_mp3_size_bytes for m in TelegramMessage
                if (m.downloaded_file_path is not None and m.download_status == Status.COMPLETED.name)
            )
            return done_count, total_count, done_bytes, total_bytes
