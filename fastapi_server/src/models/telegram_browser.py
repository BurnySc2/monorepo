from datetime import datetime
from enum import Enum

from piccolo.columns import BigInt, Bytea, DoublePrecision, ForeignKey, Integer, Text, Timestamp
from piccolo.table import Table


class TelegramChannel(Table, tablename="litestar_telegram_channel"):
    channel_id = BigInt(required=True, unique=True)
    channel_title = Text(required=True)
    channel_username = Text(required=True)
    creation_date = Timestamp(required=True)
    participants = BigInt(required=True)
    last_parsed = Timestamp(required=True, default=datetime(2000, 1, 1))


class Status(str, Enum):
    NoFile = "NoFile"
    HasFile = "HasFile"
    Queued = "Queued"
    Downloading = "Downloading"
    Downloaded = "Downloaded"


class TelegramMessage(Table, tablename="litestar_telegram_message"):
    message_id = BigInt(required=True)
    message_date = Timestamp(required=True)
    message_text = Text(required=False)
    amount_of_reactions = Integer(default=0, required=True)
    amount_of_comments = Integer(default=0, required=True)
    status = Text(default=Status.NoFile, choices=Status)  # Maybe needs to be Varchar
    file_downloadinfo_id = BigInt(required=False)
    file_downloadinfo_access_hash = BigInt(required=False)
    file_downloadinfo_file_reference = Bytea(required=False)
    downloading_start_time = Timestamp(required=False)
    mime_type = Text(required=False)
    file_extension = Text(required=False)
    file_size_bytes = Integer(required=False)
    file_duration_seconds = DoublePrecision(required=False)
    file_height = Integer(required=False)
    file_width = Integer(required=False)
    minio_object_name = Text(required=False)
    downloading_retry_attempt = Integer(default=0, required=True)
    channel = ForeignKey(references=TelegramChannel)
