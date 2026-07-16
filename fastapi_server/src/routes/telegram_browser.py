from __future__ import annotations

import os
from datetime import datetime
from typing import Annotated

import arrow
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse

from components.login.allowlist import require_allowed_user
from components.login.cookies import LoggedInUser
from models.telegram_browser import Status, TelegramChannel, TelegramDownload, TelegramMessage
from s3_helper import RUSTFS_TELEGRAM_BUCKET, get_s3_client, object_create_presigned_url, object_delete
from schemas.telegram_browser import (
    ChannelNameItem,
    DeleteFileResponse,
    DownloadedFileItem,
    QueueFileResponse,
    SearchResultItem,
    SearchResultMetadata,
    ViewFileResponse,
)

telegram_browser_router = APIRouter()


def _parse_duration_to_seconds(duration_str: str) -> int | None:
    """Convert 'HH:MM:SS' or 'MM:SS' string to total seconds. Returns None if empty/zero."""
    if not duration_str or duration_str in ("00:00:00", "00:00", "0"):
        return None
    parts = duration_str.split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if len(parts) == 2:
            return int(parts[0]) * 60 + int(parts[1])
        return None
    except (ValueError, IndexError):
        return None


def _build_message_link(channel_username: str | None, channel_id: int, message_id: int) -> str:
    """Construct a Telegram message link."""
    if channel_username:
        return f"https://t.me/{channel_username}/{message_id}"
    return f"https://t.me/c/{channel_id}/{message_id}"


def _format_search_result(row: dict) -> SearchResultItem:
    """Convert a raw DB row into the SearchResult shape expected by frontend."""
    channel_username = row.get("channel_username")
    channel_id_val = row.get("channel_id")
    message_id_val = row.get("message_id")

    message_link = ""
    if channel_id_val and message_id_val:
        message_link = _build_message_link(channel_username, channel_id_val, message_id_val)

    return SearchResultItem(
        metadata=SearchResultMetadata(
            id=str(row.get("id", "")),
            status=row.get("status", Status.NoFile),
        ),
        message_date=str(row["message_date"]) if row.get("message_date") else None,
        channel_title=row.get("channel_title"),
        channel_username=channel_username,
        message_text=row.get("message_text"),
        amount_of_reactions=row.get("amount_of_reactions", 0),
        amount_of_comments=row.get("amount_of_comments", 0),
        file_extension=row.get("file_extension"),
        file_size_bytes=row.get("file_size_bytes"),
        file_duration_seconds=row.get("file_duration_seconds"),
        file_height=row.get("file_height"),
        file_width=row.get("file_width"),
        mime_type=row.get("mime_type"),
        message_link=message_link,
    )


def _format_download_item(row: dict) -> DownloadedFileItem:
    """Convert a raw DB row (TelegramDownload + FK traversal) into a DownloadedFileItem."""
    channel_username = row.get("channel_username")
    channel_id_val = row.get("channel_id")
    message_id_val = row.get("message_id")

    message_link = ""
    if channel_id_val and message_id_val:
        message_link = _build_message_link(channel_username, channel_id_val, message_id_val)

    return DownloadedFileItem(
        # Download metadata
        download_queue_time=str(row["download_queue_time"]),
        download_start_time=str(row["download_start_time"]) if row.get("download_start_time") else None,
        download_finished_time=str(row["download_finished_time"]) if row.get("download_finished_time") else None,
        download_retry_attempt=row.get("download_retry_attempt", 0),
        s3_object_name=row.get("s3_object_name", ""),
        # Message metadata
        message_id=row.get("message_id"),
        message_date=str(row["message_date"]),
        message_text=row.get("message_text", ""),
        status=row.get("status", ""),
        # File info
        file_mime_type=row.get("file_mime_type", ""),
        file_extension=row.get("file_extension", ""),
        file_size_bytes=row.get("file_size_bytes", 0),
        file_duration_seconds=row.get("file_duration_seconds", 0.0),
        # Channel info
        channel_title=row.get("channel_title", ""),
        channel_username=channel_username or "",
        # Constructed
        message_link=message_link,
    )


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 1: GET /search
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.get("/search", response_model=list[SearchResultItem])
async def search_messages(
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
    search_text: str = Query(default=""),
    channel_name: str = Query(default=""),
    datetime_min: str = Query(default=""),
    datetime_max: str = Query(default=""),
    reactions_min: int = Query(default=0),
    reactions_max: int = Query(default=0),
    comments_min: int = Query(default=0),
    comments_max: int = Query(default=0),
    must_have_file: bool = Query(default=False),
    file_extension: str = Query(default=""),
    file_duration_min: str = Query(default="00:00:00"),
    file_duration_max: str = Query(default="00:00:00"),
    file_size_min: int = Query(default=0),
    file_size_max: int = Query(default=0),
    file_image_width_min: int = Query(default=0),
    file_image_width_max: int = Query(default=0),
    file_image_height_min: int = Query(default=0),
    file_image_height_max: int = Query(default=0),
) -> list[SearchResultItem]:
    """
    Search telegram messages with dynamic filters.
    Joins with TelegramChannel via FK traversal for channel_title.
    Returns list of SearchResult dicts (frontend expects array directly).
    """
    # Build query with implicit join via FK traversal
    query = TelegramMessage.select(  # pyrefly: ignore[missing-attribute]
        *TelegramMessage.all_columns(),
        TelegramMessage.channel.channel_id.as_alias("channel_id"),
        TelegramMessage.channel.channel_title.as_alias("channel_title"),
        TelegramMessage.channel.channel_username.as_alias("channel_username"),
    )

    # Apply filters dynamically
    if search_text:
        query = query.where(TelegramMessage.message_text.ilike(f"%{search_text}%"))

    if channel_name:
        query = query.where(TelegramMessage.channel.channel_title.ilike(f"%{channel_name}%"))

    if datetime_min:
        try:
            dt_min = datetime.fromisoformat(datetime_min)
            query = query.where(TelegramMessage.message_date >= dt_min)
        except ValueError:
            pass

    if datetime_max:
        try:
            dt_max = datetime.fromisoformat(datetime_max)
            query = query.where(TelegramMessage.message_date <= dt_max)
        except ValueError:
            pass

    if reactions_min > 0:
        query = query.where(TelegramMessage.amount_of_reactions >= reactions_min)

    if reactions_max > 0:
        query = query.where(TelegramMessage.amount_of_reactions <= reactions_max)

    if comments_min > 0:
        query = query.where(TelegramMessage.amount_of_comments >= comments_min)

    if comments_max > 0:
        query = query.where(TelegramMessage.amount_of_comments <= comments_max)

    if must_have_file:
        query = query.where(TelegramMessage.status != Status.NoFile)

    if file_extension:
        query = query.where(TelegramMessage.file_extension.ilike(f"%{file_extension}%"))

    # Duration filters (convert "HH:MM:SS" -> seconds)
    duration_min_seconds = _parse_duration_to_seconds(file_duration_min)
    if duration_min_seconds is not None and duration_min_seconds > 0:
        query = query.where(TelegramMessage.file_duration_seconds >= duration_min_seconds)

    duration_max_seconds = _parse_duration_to_seconds(file_duration_max)
    if duration_max_seconds is not None and duration_max_seconds > 0:
        query = query.where(TelegramMessage.file_duration_seconds <= duration_max_seconds)

    # File size filters (frontend sends MB -> convert to bytes)
    if file_size_min > 0:
        query = query.where(TelegramMessage.file_size_bytes >= file_size_min * 1024 * 1024)

    if file_size_max > 0:
        query = query.where(TelegramMessage.file_size_bytes <= file_size_max * 1024 * 1024)

    # Image dimension filters
    if file_image_width_min > 0:
        query = query.where(TelegramMessage.file_width >= file_image_width_min)

    if file_image_width_max > 0:
        query = query.where(TelegramMessage.file_width <= file_image_width_max)

    if file_image_height_min > 0:
        query = query.where(TelegramMessage.file_height >= file_image_height_min)

    if file_image_height_max > 0:
        query = query.where(TelegramMessage.file_height <= file_image_height_max)

    # Apply ordering and limit (no pagination - frontend expects array)
    rows = await query.order_by(TelegramMessage.message_date, ascending=False).limit(1000)

    return [_format_search_result(row) for row in rows]


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 2: GET /queue-file/{id}
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.get("/queue-file/{id}", response_model=QueueFileResponse)
async def queue_file(
    id: int,
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
) -> QueueFileResponse:
    """
    Queue a file for download.
    Only succeeds if current status is 'HasFile'.
    """
    message = (
        await TelegramMessage.objects().where(TelegramMessage.id == id).first()
    )  # pyrefly: ignore[missing-attribute]

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.status != Status.HasFile:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot queue file with status '{message.status}'. Must be 'HasFile'.",
        )

    message.status = Status.Queued
    await message.save()

    return QueueFileResponse(queued=True)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 3: DELETE /delete-file/{id}
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.delete("/delete-file/{id}", response_model=DeleteFileResponse)
async def delete_file(
    id: int,
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
) -> DeleteFileResponse:
    """
    Delete a downloaded file from S3 and reset status to 'HasFile'.
    Deletes from S3 if s3_object_name exists (regardless of status).
    Removes the download record and resets message status.
    """
    message = (
        await TelegramMessage.objects().where(TelegramMessage.id == id).first()
    )  # pyrefly: ignore[missing-attribute]

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get the download record
    download = await TelegramDownload.objects().where(TelegramDownload.message == id).first()

    if download is not None:
        # Delete S3 object if it exists
        if download.s3_object_name:
            async with get_s3_client() as s3:
                await object_delete(s3, RUSTFS_TELEGRAM_BUCKET, download.s3_object_name)

        # Delete the download record
        await download.remove()

    # Reset message status
    message.status = Status.HasFile
    await message.save()

    return DeleteFileResponse(deleted=True)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 4: GET /view-file/{id}
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.get("/view-file/{id}", response_model=ViewFileResponse)
async def view_file(
    id: int,
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
) -> ViewFileResponse:
    """
    Get a presigned S3 URL for viewing a file.
    Only succeeds if status is 'Downloaded' and s3_object_name exists.
    """
    message = (
        await TelegramMessage.objects().where(TelegramMessage.id == id).first()
    )  # pyrefly: ignore[missing-attribute]

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get the download record
    download = await TelegramDownload.objects().where(TelegramDownload.message == id).first()

    if message.status != Status.Downloaded or download is None or not download.s3_object_name:
        raise HTTPException(
            status_code=400,
            detail="File not available for viewing. Must be 'Downloaded'.",
        )

    file_name = f"telegram_{message.channel}_{message.message_id}"
    if message.file_extension:
        file_name += f".{message.file_extension}"

    async with get_s3_client() as s3:
        presigned_url = await object_create_presigned_url(
            session=s3,
            bucket=RUSTFS_TELEGRAM_BUCKET,
            key=download.s3_object_name,
            file_name=file_name,
            expires_in_seconds=3600,
            verify_object_exists=True,
            disposition="inline",  # View inline, not as download
        )

    if presigned_url is None:
        raise HTTPException(status_code=404, detail="File not found in storage")

    return ViewFileResponse(
        minio_url=presigned_url,
        mime_type=message.file_mime_type or "application/octet-stream",
    )


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 5: GET /download-file/{id}
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.get("/download-file/{id}")
async def download_file(
    id: int,
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
) -> RedirectResponse:
    """
    Redirect to a presigned S3 URL with Content-Disposition: attachment.
    Used as an <a href> link for browser downloads.
    """
    message = (
        await TelegramMessage.objects().where(TelegramMessage.id == id).first()
    )  # pyrefly: ignore[missing-attribute]

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    # Get the download record
    download = await TelegramDownload.objects().where(TelegramDownload.message == id).first()

    if message.status != Status.Downloaded or download is None or not download.s3_object_name:
        raise HTTPException(
            status_code=400,
            detail="File not available for download. Must be 'Downloaded'.",
        )

    file_name = f"telegram_{message.channel}_{message.message_id}"
    if message.file_extension:
        file_name += f".{message.file_extension}"

    async with get_s3_client() as s3:
        presigned_url = await object_create_presigned_url(
            session=s3,
            bucket=RUSTFS_TELEGRAM_BUCKET,
            key=download.s3_object_name,
            file_name=file_name,
            expires_in_seconds=3600,
            verify_object_exists=True,
        )

    if presigned_url is None:
        raise HTTPException(status_code=404, detail="File not found in storage")

    return RedirectResponse(url=presigned_url, status_code=302)


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 6: GET /channel-names
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.get("/channel-names", response_model=list[ChannelNameItem])
async def get_channel_names(
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
) -> list[ChannelNameItem]:
    """
    Get all channels that have a username set.
    Returns a list of channel titles and usernames, ordered alphabetically by title.
    """
    channels = (
        await TelegramChannel.select(
            TelegramChannel.channel_title,
            TelegramChannel.channel_username,
        )
        .where(TelegramChannel.channel_username.is_not_null())
        .order_by(TelegramChannel.channel_title)
    )

    return [
        ChannelNameItem(
            channel_title=row["channel_title"],
            channel_username=row["channel_username"],
        )
        for row in channels
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 7: GET /downloads
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.get("/downloads", response_model=list[DownloadedFileItem])
async def list_downloads(
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
) -> list[DownloadedFileItem]:
    """
    List all downloaded files from the last N days.
    Joins TelegramDownload -> TelegramMessage -> TelegramChannel via FK traversal.
    """
    # Get expiration period from environment (default 7 days)
    try:
        expiration_days = int(os.getenv("RUSTFS_TELEGRAM_BUCKET_EXPIRATION_DAYS", "7"))
    except ValueError:
        expiration_days = 7
    cutoff_time = arrow.now().shift(days=-expiration_days).naive

    # Query downloads completed within the expiration window
    rows = (
        await TelegramDownload.select(  # pyrefly: ignore[missing-attribute]
            *TelegramDownload.all_columns(),
            TelegramDownload.message.message_id.as_alias("message_id"),
            TelegramDownload.message.message_date.as_alias("message_date"),
            TelegramDownload.message.message_text.as_alias("message_text"),
            TelegramDownload.message.status.as_alias("status"),
            TelegramDownload.message.file_mime_type.as_alias("file_mime_type"),
            TelegramDownload.message.file_extension.as_alias("file_extension"),
            TelegramDownload.message.file_size_bytes.as_alias("file_size_bytes"),
            TelegramDownload.message.file_duration_seconds.as_alias("file_duration_seconds"),
            TelegramDownload.message.channel.channel_id.as_alias("channel_id"),
            TelegramDownload.message.channel.channel_title.as_alias("channel_title"),
            TelegramDownload.message.channel.channel_username.as_alias("channel_username"),
        )
        .where(TelegramDownload.download_finished_time >= cutoff_time)
        .order_by(TelegramDownload.download_queue_time, ascending=False)
        .limit(1000)
    )

    return [_format_download_item(row) for row in rows]
