from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SearchResultMetadata(BaseModel):
    id: str
    status: str


class SearchResultItem(BaseModel):
    metadata: SearchResultMetadata
    message_date: str | None = None
    channel_title: str | None = None
    channel_username: str | None = None
    message_text: str | None = None
    amount_of_reactions: int = 0
    amount_of_comments: int = 0
    file_extension: str | None = None
    file_size_bytes: int | None = None
    file_duration_seconds: float | None = None
    file_height: int | None = None
    file_width: int | None = None
    mime_type: str | None = None
    message_link: str = ""


class QueueFileResponse(BaseModel):
    queued: bool


class DeleteFileResponse(BaseModel):
    deleted: bool


class ViewFileResponse(BaseModel):
    minio_url: str
    mime_type: str


SortColumn = Literal[
    "message_date",
    "amount_of_reactions",
    "amount_of_comments",
    "file_size_bytes",
    "file_duration_seconds",
    "file_height",
    "file_width",
    "channel_title",
    "channel_username",
    "file_extension",
    "mime_type",
]


class SortItem(BaseModel):
    column: SortColumn
    ascending: bool = True


class SearchRequest(BaseModel):
    search_text: str = ""
    channel_name: str = ""
    datetime_min: str = ""
    datetime_max: str = ""
    reactions_min: int = 0
    reactions_max: int = 0
    comments_min: int = 0
    comments_max: int = 0
    must_have_file: bool = False
    file_extension: str = ""
    file_duration_min: str = "00:00:00"
    file_duration_max: str = "00:00:00"
    file_size_min: int = 0
    file_size_max: int = 0
    file_image_width_min: int = 0
    file_image_width_max: int = 0
    file_image_height_min: int = 0
    file_image_height_max: int = 0
    sort: list[SortItem] = []


class ChannelNameItem(BaseModel):
    channel_title: str
    channel_username: str


class ChannelStatsItem(BaseModel):
    channel_title: str
    channel_username: str
    creation_date: str
    participants: int
    total_messages: int
    total_files: int


class DownloadedFileItem(BaseModel):
    # From TelegramDownload
    download_queue_time: str
    download_start_time: str | None = None
    download_finished_time: str | None = None
    download_retry_attempt: int
    s3_object_name: str

    # From TelegramMessage
    message_id: int
    message_date: str
    message_text: str
    status: str
    file_mime_type: str
    file_extension: str
    file_size_bytes: int
    file_duration_seconds: float

    # From TelegramChannel
    channel_title: str
    channel_username: str

    # Constructed
    message_link: str
