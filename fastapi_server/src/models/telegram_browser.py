from enum import Enum

from piccolo.columns import Bytea, ForeignKey, Integer, Text, Timestamptz
from piccolo.table import Table


# await AudiobookBook.create_table(if_not_exists=True)
# await AudiobookChapter.create_table(if_not_exists=True)
class TelegramChannel(Table, tablename="litestar_telegram_channel"):
    channel_id = Integer(required=True, unique=True)
    channel_title = Text(required=True)
    channel_username = Text(required=False)
    creation_date = Timestamptz(required=True)
    participants = Integer(required=True)
    last_parsed = Timestamptz(required=True)


class Status(str, Enum):
    NoFile = "NoFile"
    HasFile = "HasFile"
    Queued = "Queued"
    Downloading = "Downloading"
    Downloaded = "Downloaded"


class TelegramMessage(Table, tablename="litestar_telegram_message"):
    channel_id = Integer(required=True)
    message_id = Integer(required=True)
    message_date = Timestamptz(required=True)
    message_text = Text(required=False)
    amount_of_reactions = Integer(default=0, required=True)
    amount_of_comments = Integer(default=0, required=True)
    status = Text(default=Status.NoFile, choices=Status)  # Maybe needs to be Varchar
    file_downloadinfo_id = Integer(required=False)
    file_downloadinfo_access_hash = Integer(required=False)
    file_downloadinfo_file_reference = Bytea(required=False)
    downloading_start_time = Timestamptz(required=False)
    mime_type = Text(required=False)
    file_extension = Text(required=False)
    file_size_bytes = Integer(required=False)
    file_duration_seconds = Integer(required=False)
    file_height = Integer(required=False)
    file_width = Integer(required=False)
    minio_object_name = Text(required=False)
    downloading_retry_attempt = Integer(default=0, required=True)
    channel = ForeignKey(references=TelegramChannel)
