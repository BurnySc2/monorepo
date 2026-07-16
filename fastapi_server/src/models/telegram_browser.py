from datetime import datetime
from enum import Enum

import arrow
from piccolo.columns import BigInt, Bytea, DoublePrecision, ForeignKey, Integer, Text, Timestamp
from piccolo.table import Table


class TelegramChannel(Table, tablename="litestar_telegram_channel"):
    channel_id = BigInt(required=True, primary_key=True)
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
    channel = ForeignKey(references=TelegramChannel)
    message_id = BigInt(required=True)
    message_date = Timestamp(required=True)
    message_text = Text(default="", required=False)
    amount_of_reactions = Integer(default=0, required=True)
    amount_of_comments = Integer(default=0, required=True)
    status = Text(default=Status.NoFile, choices=Status)
    file_downloadinfo_id = BigInt(default=0, required=False)
    file_downloadinfo_access_hash = BigInt(default=0, required=False)
    file_downloadinfo_file_reference = Bytea(default=b"", required=False)
    file_mime_type = Text(default="", required=False)
    file_extension = Text(default="", required=False)
    file_size_bytes = Integer(default=0, required=False)
    file_duration_seconds = DoublePrecision(default=0, required=False)
    file_height = Integer(default=0, required=False)
    file_width = Integer(default=0, required=False)


class TelegramDownload(Table, tablename="litestar_telegram_download"):
    message = ForeignKey(references=TelegramMessage)
    download_queue_time = Timestamp(default=lambda: arrow.now().naive, required=False)
    download_start_time = Timestamp(default=None, required=False, null=True)
    download_finished_time = Timestamp(default=None, required=False, null=True)
    download_retry_attempt = Integer(default=0, required=False)
    s3_object_name = Text(default="", required=False)
