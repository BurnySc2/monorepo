from __future__ import annotations

import datetime
import enum

from pony import orm  # pyre-fixme[21]

from src.secrets_loader import SECRETS

db = orm.Database()

# Create connection
db.bind(provider="sqlite", filename="../messages.db", create_db=True)


def photo_filter(message: MessageModel) -> bool:
    # Returns True if it fits the criteria (= should be downloaded)
    if message.media_type != "Photo":
        return True
    if "Photo" not in SECRETS.media_types:
        return False
    return all(
        [
            SECRETS.photo_min_file_size_bytes <= message.file_size_bytes <= SECRETS.photo_max_file_size_bytes,
            SECRETS.photo_min_width <= message.file_width <= SECRETS.photo_max_width,
            SECRETS.photo_min_height <= message.file_height <= SECRETS.photo_max_height,
        ]
    )


def video_filter(message: MessageModel) -> bool:
    # Returns True if it fits the criteria (= should be downloaded)
    if message.media_type != "Video":
        return True
    if "Video" not in SECRETS.media_types:
        return False
    return all(
        [
            SECRETS.video_min_file_size_bytes <= message.file_size_bytes <= SECRETS.video_max_file_size_bytes,
            SECRETS.video_min_file_duration_seconds <= message.file_duration_seconds <=
            SECRETS.video_max_file_duration_seconds,
            SECRETS.video_min_width <= message.file_width <= SECRETS.video_max_width,
            SECRETS.video_min_height <= message.file_height <= SECRETS.video_max_height,
        ]
    )


def audio_filter(message: MessageModel) -> bool:
    # Returns True if it fits the criteria (= should be downloaded)
    if message.media_type != "Audio":
        return True
    if "Audio" not in SECRETS.media_types:
        return False
    return all(
        [
            SECRETS.audio_min_file_size_bytes <= message.file_size_bytes <= SECRETS.audio_max_file_size_bytes,
            SECRETS.audio_min_file_duration_seconds <= message.file_duration_seconds <=
            SECRETS.audio_max_file_duration_seconds
        ]
    )


class Status(enum.Enum):
    """Possible status of a message in the db."""
    UNKNOWN = 0
    QUEUED = 1
    FILTERED = 2
    DOWNLOADING = 3
    MISSING_FILE_NAME = 4
    NO_MEDIA = 5
    COMPLETED = 6


class MessageModel(db.Entity):
    id = orm.PrimaryKey(int, auto=True)
    channel_id = orm.Required(str)
    message_id = orm.Required(int)
    message_date = orm.Required(datetime.datetime)
    link = orm.Required(str)
    status = orm.Required(str)
    retry = orm.Required(int)
    output_file = orm.Optional(str)
    media_type = orm.Optional(str)
    file_id = orm.Optional(str)
    file_unique_id = orm.Optional(str)
    file_name = orm.Optional(str)
    file_size_bytes = orm.Optional(int)
    file_duration_seconds = orm.Optional(int)
    file_height = orm.Optional(int)
    file_width = orm.Optional(int)

    @staticmethod
    def get_one_queued() -> MessageModel | None:
        """Used in getting any queued message for the download-worker."""
        with orm.db_session():
            messages = orm.select(m for m in MessageModel if m.status == Status.QUEUED.name
                                  ).order_by(orm.desc(MessageModel.message_id)).limit(1)
            if len(messages) == 0:
                return None
            return list(messages)[0]

    @staticmethod
    def get_oldest_message_id(channel_id: str) -> int:
        """Used in finding the oldest parsed message_id of a channel. Returns 0 if channel has not been parsed yet."""
        with orm.db_session():
            messages = orm.select(m for m in MessageModel
                                  if m.channel_id == channel_id).order_by(MessageModel.message_id).limit(1)
            if len(messages) == 0:
                return 0
            return list(messages)[0].message_id

    @staticmethod
    def get_count() -> tuple[int, int]:
        """Returns a tuple of how many downloads are complete and how many total there are."""
        with orm.db_session():
            done_count = orm.count(m for m in MessageModel if m.status == Status.COMPLETED.name)
            total_count = orm.count(
                m for m in MessageModel if m.status in [
                    Status.QUEUED.name,
                    Status.DOWNLOADING.name,
                    Status.COMPLETED.name,
                ]
            )
            return done_count, total_count


# Enable debug mode to see the queries sent
# orm.set_sql_debug(True)

# Create tables if they didn't exist yet
db.generate_mapping(create_tables=True)
