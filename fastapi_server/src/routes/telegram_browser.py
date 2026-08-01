from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from typing import Annotated

import arrow
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import RedirectResponse

from components.login.allowlist import require_allowed_user
from components.login.cookies import LoggedInUser
from models.telegram_browser import DownloadStatus, Status, TelegramChannel, TelegramDownload, TelegramMessage
from s3_helper import RUSTFS_TELEGRAM_BUCKET, get_s3_client, object_create_presigned_url, object_delete
from schemas.telegram_browser import (
    ChannelNameItem,
    ChannelStatsItem,
    DeleteFileResponse,
    DownloadedFileItem,
    QueueFileResponse,
    SearchRequest,
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


def _format_search_result(row: dict, download_status_map: dict[int, str]) -> SearchResultItem:
    """Convert a raw DB row into the SearchResult shape expected by frontend."""
    channel_username = row.get("channel_username")
    channel_id_val = row.get("channel_id")
    message_id_val = row.get("message_id")

    message_link = ""
    if channel_id_val and message_id_val:
        message_link = _build_message_link(channel_username, channel_id_val, message_id_val)

    download_status = download_status_map.get(row.get("id"))

    return SearchResultItem(
        metadata=SearchResultMetadata(
            id=str(row.get("id", "")),
            status=row.get("status", Status.NoFile),
            download_status=download_status,
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
        message_id=row.get("message_id"),  # pyrefly: ignore[bad-argument-type]
        message_date=str(row["message_date"]),
        message_text=row.get("message_text", ""),
        download_status=row.get("download_status", ""),
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
# Endpoint 1: POST /search
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.post("/search", response_model=list[SearchResultItem])
async def search_messages(
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
    request: SearchRequest,
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
    if request.search_text:
        query = query.where(TelegramMessage.message_text.ilike(f"%{request.search_text}%"))

    if request.channel_name:
        query = query.where(TelegramMessage.channel.channel_title.ilike(f"%{request.channel_name}%"))

    if request.datetime_min:
        try:
            dt_min = datetime.fromisoformat(request.datetime_min)
            query = query.where(TelegramMessage.message_date >= dt_min)
        except ValueError:
            pass

    if request.datetime_max:
        try:
            dt_max = datetime.fromisoformat(request.datetime_max)
            query = query.where(TelegramMessage.message_date <= dt_max)
        except ValueError:
            pass

    if request.reactions_min > 0:
        query = query.where(TelegramMessage.amount_of_reactions >= request.reactions_min)

    if request.reactions_max > 0:
        query = query.where(TelegramMessage.amount_of_reactions <= request.reactions_max)

    if request.comments_min > 0:
        query = query.where(TelegramMessage.amount_of_comments >= request.comments_min)

    if request.comments_max > 0:
        query = query.where(TelegramMessage.amount_of_comments <= request.comments_max)

    if request.must_have_file:
        query = query.where(TelegramMessage.status != Status.NoFile)

    if request.file_extension:
        query = query.where(TelegramMessage.file_extension.ilike(f"%{request.file_extension}%"))

    # Duration filters (convert "HH:MM:SS" -> seconds)
    duration_min_seconds = _parse_duration_to_seconds(request.file_duration_min)
    if duration_min_seconds is not None and duration_min_seconds > 0:
        query = query.where(TelegramMessage.file_duration_seconds >= duration_min_seconds)

    duration_max_seconds = _parse_duration_to_seconds(request.file_duration_max)
    if duration_max_seconds is not None and duration_max_seconds > 0:
        query = query.where(TelegramMessage.file_duration_seconds <= duration_max_seconds)

    # File size filters (frontend sends MB -> convert to bytes)
    if request.file_size_min > 0:
        query = query.where(TelegramMessage.file_size_bytes >= request.file_size_min * 1024 * 1024)

    if request.file_size_max > 0:
        query = query.where(TelegramMessage.file_size_bytes <= request.file_size_max * 1024 * 1024)

    # Image dimension filters
    if request.file_image_width_min > 0:
        query = query.where(TelegramMessage.file_width >= request.file_image_width_min)

    if request.file_image_width_max > 0:
        query = query.where(TelegramMessage.file_width <= request.file_image_width_max)

    if request.file_image_height_min > 0:
        query = query.where(TelegramMessage.file_height >= request.file_image_height_min)

    if request.file_image_height_max > 0:
        query = query.where(TelegramMessage.file_height <= request.file_image_height_max)

    # Map SortColumn string values to Piccolo columns
    allowed_sort_columns = {
        "message_date": TelegramMessage.message_date,
        "amount_of_reactions": TelegramMessage.amount_of_reactions,
        "amount_of_comments": TelegramMessage.amount_of_comments,
        "file_size_bytes": TelegramMessage.file_size_bytes,
        "file_duration_seconds": TelegramMessage.file_duration_seconds,
        "file_height": TelegramMessage.file_height,
        "file_width": TelegramMessage.file_width,
        "channel_title": TelegramMessage.channel.channel_title,
        "channel_username": TelegramMessage.channel.channel_username,
        "file_extension": TelegramMessage.file_extension,
        "mime_type": TelegramMessage.file_mime_type,
    }

    # Apply ordering - call order_by per column to support mixed ascending/descending
    if request.sort:
        for item in request.sort:
            col = allowed_sort_columns[item.column]
            query = query.order_by(col, ascending=item.ascending)
    else:
        query = query.order_by(TelegramMessage.message_date, ascending=False)

    rows = await query.limit(1000)

    # Batch-fetch download statuses for all returned messages
    message_ids = [row["id"] for row in rows]
    download_status_map: dict[int, str] = {}
    if message_ids:
        downloads = await TelegramDownload.select(
            TelegramDownload.message,
            TelegramDownload.status,
        ).where(TelegramDownload.message.is_in(message_ids))
        for dl in downloads:
            download_status_map[dl["message"]] = dl["status"]

    return [_format_search_result(row, download_status_map) for row in rows]


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
    Creates a TelegramDownload record with status=Queued.
    Returns 409 if an active download (Queued/Downloading) already exists.
    Deletes and recreates if a terminal download (Downloaded/Failed/GiveUp) exists.
    Does NOT modify TelegramMessage.status.
    """
    message = await (
        TelegramMessage.objects().where(TelegramMessage.id == id).first()  # pyrefly: ignore[missing-attribute]
    )

    if message is None:
        raise HTTPException(status_code=404, detail="Message not found")

    if message.status != Status.HasFile:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot queue file with status '{message.status}'. Must be 'HasFile'.",
        )

    # Check for existing download record
    existing_download = await TelegramDownload.objects().where(TelegramDownload.message == id).first()

    if existing_download is not None:
        if existing_download.status in (DownloadStatus.Queued, DownloadStatus.Downloading):
            raise HTTPException(
                status_code=409,
                detail=f"Download already active with status '{existing_download.status}'.",
            )
        # Terminal state (Downloaded/Failed/GiveUp) — delete old record and recreate
        await existing_download.remove()

    # Create new download record
    await TelegramDownload(
        message=id,
        status=DownloadStatus.Queued,
    ).save()

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
    Delete a downloaded file from S3 and remove the download record.
    Message status is no longer modified — it stays as 'HasFile'.
    """
    message = await (
        TelegramMessage.objects().where(TelegramMessage.id == id).first()  # pyrefly: ignore[missing-attribute]
    )

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
    # Get the download record
    download = (
        await TelegramDownload.objects()
        .prefetch(TelegramDownload.message)
        .where(TelegramDownload.message.id == id)
        .first()
    )

    if download is None:
        raise HTTPException(status_code=404, detail="Message not found")

    if download.status != DownloadStatus.Downloaded or not download.s3_object_name:
        raise HTTPException(
            status_code=400,
            detail="File not available for viewing. Must be 'Downloaded'.",
        )

    file_name = (
        f"telegram_{download.message.channel}_{download.message.id}{download.message.file_extension}"
    )

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
        mime_type=download.message.file_mime_type or "application/octet-stream",
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
    # Get the download record
    download = (
        await TelegramDownload.objects()
        .prefetch(TelegramDownload.message)
        .where(TelegramDownload.message == id)
        .first()
    )

    if download is None:
        raise HTTPException(status_code=404, detail="Message not found")

    if download is None or download.status != DownloadStatus.Downloaded or not download.s3_object_name:
        raise HTTPException(
            status_code=400,
            detail="File not available for download. Must be 'Downloaded'.",
        )

    file_name = f"telegram_{download.message.channel}_{download.message.id}{download.message.file_extension}"

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
# Endpoint 7: GET /channel-stats
# ──────────────────────────────────────────────────────────────────────────────
@telegram_browser_router.get("/channel-stats", response_model=list[ChannelStatsItem])
async def get_channel_stats(
    current_user: Annotated[LoggedInUser, Depends(require_allowed_user)],
) -> list[ChannelStatsItem]:
    """
    Get statistics for all telegram channels.
    Returns channel info with message counts and file counts, sorted by total messages descending.
    """
    query = (Path(__file__).parent.parent / "queries" / "telegram_browser_channel_stats.sql").read_text()
    rows: list[dict] = await TelegramChannel.raw(query)  # pyrefly: ignore[missing-attribute]

    return [
        ChannelStatsItem(
            channel_title=row["channel_title"],
            channel_username=row["channel_username"],
            creation_date=str(row["creation_date"]),
            participants=row["participants"],
            total_messages=row["total_messages"],
            total_files=row["total_files"],
        )
        for row in rows
    ]


# ──────────────────────────────────────────────────────────────────────────────
# Endpoint 8: GET /downloads
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
            TelegramDownload.message.id.as_alias("message_id"),
            TelegramDownload.message.message_date.as_alias("message_date"),
            TelegramDownload.message.message_text.as_alias("message_text"),
            TelegramDownload.status.as_alias("download_status"),
            TelegramDownload.message.file_mime_type.as_alias("file_mime_type"),
            TelegramDownload.message.file_extension.as_alias("file_extension"),
            TelegramDownload.message.file_size_bytes.as_alias("file_size_bytes"),
            TelegramDownload.message.file_duration_seconds.as_alias("file_duration_seconds"),
            (
                TelegramDownload.message.channel.channel_id  # pyrefly: ignore[missing-attribute]
            ).as_alias("channel_id"),
            (
                TelegramDownload.message.channel.channel_title  # pyrefly: ignore[missing-attribute]
            ).as_alias("channel_title"),
            (
                TelegramDownload.message.channel.channel_username  # pyrefly: ignore[missing-attribute]
            ).as_alias("channel_username"),
        )
        .where(TelegramDownload.status == DownloadStatus.Downloaded)
        .where(TelegramDownload.download_finished_time >= cutoff_time)
        .order_by(TelegramDownload.download_queue_time, ascending=False)
        .limit(1000)
    )

    return [_format_download_item(row) for row in rows]
