"""Tests for GET /telegram-browser/downloads endpoint."""

from datetime import datetime

import arrow
from fastapi.testclient import TestClient

from models.telegram_browser import DownloadStatus, TelegramChannel, TelegramDownload, TelegramMessage

_CHANNEL_TABLE = TelegramChannel._meta.tablename
_MESSAGE_TABLE = TelegramMessage._meta.tablename


def _create_channel(
    channel_id: int,
    title: str,
    username: str | None = None,
) -> None:
    """Create a TelegramChannel record."""
    if username is not None:
        channel = TelegramChannel(
            channel_id=channel_id,
            channel_title=title,
            channel_username=username,
            creation_date=datetime(2024, 1, 1),
            participants=100,
            last_parsed=datetime(2024, 1, 1),
        )
        channel.save().run_sync()
    else:
        # Temporarily drop NOT NULL constraint to insert NULL username
        TelegramChannel.raw(f"ALTER TABLE {_CHANNEL_TABLE} ALTER COLUMN channel_username DROP NOT NULL").run_sync()
        channel = TelegramChannel(
            channel_id=channel_id,
            channel_title=title,
            channel_username=None,
            creation_date=datetime(2024, 1, 1),
            participants=100,
            last_parsed=datetime(2024, 1, 1),
        )
        channel.save().run_sync()


def _create_message(
    channel_id: int,
    message_id: int,
    message_text: str = "Test message",
    status: str = "HasFile",
    file_extension: str = "mp4",
    file_mime_type: str = "video/mp4",
    file_size_bytes: int = 1024000,
    file_duration_seconds: float = 120.5,
) -> TelegramMessage:
    """Create a TelegramMessage record and return it."""
    message = TelegramMessage(
        channel=channel_id,
        message_id=message_id,
        message_date=datetime(2024, 6, 15),
        message_text=message_text,
        amount_of_reactions=5,
        amount_of_comments=2,
        status=status,
        file_extension=file_extension,
        file_mime_type=file_mime_type,
        file_size_bytes=file_size_bytes,
        file_duration_seconds=file_duration_seconds,
    )
    message.save().run_sync()
    return message


def _create_download(
    message_id: int,
    s3_object_name: str = "test-file.mp4",
    status: str = DownloadStatus.Downloaded,
    download_queue_time: datetime | None = None,
    download_start_time: datetime | None = None,
    download_finished_time: datetime | None = None,
    download_retry_attempt: int = 0,
    set_null_finished: bool = False,
) -> TelegramDownload:
    """Create a TelegramDownload record and return it.

    Defaults to ``DownloadStatus.Downloaded`` so download helpers work for
    ``/downloads``, ``/view-file`` and ``/download-file`` success tests.

    Use ``set_null_finished=True`` to explicitly store a NULL
    ``download_finished_time`` (the default ``None`` value for the parameter
    still falls back to ``arrow.now()`` for convenience).
    """
    download = TelegramDownload(
        message=message_id,
        status=status,
        download_queue_time=download_queue_time or arrow.now().naive,
        download_start_time=download_start_time,
        download_finished_time=None if set_null_finished else (download_finished_time or arrow.now().naive),
        download_retry_attempt=download_retry_attempt,
        s3_object_name=s3_object_name,
    )
    download.save().run_sync()
    return download


# ─── Happy Path ───────────────────────────────────────────────────────────────


def test_downloads_empty(telegram_client: TestClient) -> None:
    """No downloads in DB → returns empty list."""
    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_downloads_with_data(telegram_client: TestClient) -> None:
    """Create TelegramChannel, TelegramMessage, TelegramDownload → returns formatted list."""
    _create_channel(channel_id=100, title="Test Channel", username="testchan")
    msg = _create_message(channel_id=100, message_id=42, message_text="Hello world")
    _create_download(message_id=msg.id, s3_object_name="test-file.mp4")

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message_text"] == "Hello world"
    assert data[0]["channel_title"] == "Test Channel"
    assert data[0]["channel_username"] == "testchan"
    assert data[0]["s3_object_name"] == "test-file.mp4"
    assert data[0]["message_id"] == msg.id  # internal TelegramMessage PK


# ─── Filtering by finished time ──────────────────────────────────────────────


def test_downloads_filtering_by_finished_time(telegram_client: TestClient) -> None:
    """Only downloads within expiration window (7 days) are returned."""
    _create_channel(channel_id=200, title="Channel A", username="ch_a")
    _create_channel(channel_id=201, title="Channel B", username="ch_b")

    # Recent download (within 7 days) - should be returned
    msg_recent = _create_message(channel_id=200, message_id=101, message_text="Recent")
    _create_download(
        message_id=msg_recent.id,
        s3_object_name="recent.mp4",
        download_finished_time=arrow.now().shift(days=-2).naive,
    )

    # Old download (older than 7 days) - should NOT be returned
    msg_old = _create_message(channel_id=201, message_id=102, message_text="Old")
    _create_download(
        message_id=msg_old.id,
        s3_object_name="old.mp4",
        download_finished_time=arrow.now().shift(days=-10).naive,
    )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message_text"] == "Recent"
    assert data[0]["s3_object_name"] == "recent.mp4"


def test_downloads_all_expired_returns_empty(telegram_client: TestClient) -> None:
    """When all downloads are older than expiration, returns empty list."""
    _create_channel(channel_id=300, title="Expired Channel", username="expired_ch")
    msg = _create_message(channel_id=300, message_id=201, message_text="Very old")
    _create_download(
        message_id=msg.id,
        s3_object_name="old.mp4",
        download_finished_time=arrow.now().shift(days=-30).naive,
    )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


def test_downloads_null_finished_time_excluded(telegram_client: TestClient) -> None:
    """Downloads with NULL download_finished_time are excluded."""
    _create_channel(channel_id=310, title="Null Channel", username="null_ch")
    msg = _create_message(channel_id=310, message_id=301, message_text="No finish time")
    _create_download(
        message_id=msg.id,
        s3_object_name="pending.mp4",
        set_null_finished=True,
    )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0


# ─── Ordering ─────────────────────────────────────────────────────────────────


def test_downloads_ordering(telegram_client: TestClient) -> None:
    """Downloads ordered by download_queue_time descending."""
    _create_channel(channel_id=400, title="Order Channel", username="order_ch")

    # Create messages and downloads with different queue times
    msg1 = _create_message(channel_id=400, message_id=401, message_text="First queued")
    _create_download(
        message_id=msg1.id,
        s3_object_name="first.mp4",
        download_queue_time=arrow.now().shift(hours=-5).naive,
        download_finished_time=arrow.now().shift(hours=-4).naive,
    )

    msg2 = _create_message(channel_id=400, message_id=402, message_text="Second queued")
    _create_download(
        message_id=msg2.id,
        s3_object_name="second.mp4",
        download_queue_time=arrow.now().shift(hours=-2).naive,
        download_finished_time=arrow.now().shift(hours=-1).naive,
    )

    msg3 = _create_message(channel_id=400, message_id=403, message_text="Third queued")
    _create_download(
        message_id=msg3.id,
        s3_object_name="third.mp4",
        download_queue_time=arrow.now().naive,
        download_finished_time=arrow.now().naive,
    )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    # Should be in descending order (newest first)
    assert data[0]["message_text"] == "Third queued"
    assert data[1]["message_text"] == "Second queued"
    assert data[2]["message_text"] == "First queued"


# ─── Response schema shape ───────────────────────────────────────────────────


def test_downloads_includes_all_fields(telegram_client: TestClient) -> None:
    """Verify all fields from DownloadedFileItem are populated correctly."""
    _create_channel(channel_id=500, title="Full Channel", username="full_ch")
    msg = _create_message(
        channel_id=500,
        message_id=501,
        message_text="Full test message",
        status="HasFile",
        file_extension="mp4",
        file_mime_type="video/mp4",
        file_size_bytes=5242880,
        file_duration_seconds=180.0,
    )
    _create_download(
        message_id=msg.id,
        s3_object_name="full-test.mp4",
        download_queue_time=arrow.now().shift(hours=-3).naive,
        download_start_time=arrow.now().shift(hours=-2).naive,
        download_finished_time=arrow.now().shift(hours=-1).naive,
        download_retry_attempt=1,
    )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    item = data[0]
    # Download metadata fields
    assert "download_queue_time" in item
    assert "download_start_time" in item
    assert "download_finished_time" in item
    assert "download_retry_attempt" in item
    assert "s3_object_name" in item

    # Message metadata fields
    assert "message_id" in item
    assert "message_date" in item
    assert "message_text" in item
    assert "download_status" in item

    # File info fields
    assert "file_mime_type" in item
    assert "file_extension" in item
    assert "file_size_bytes" in item
    assert "file_duration_seconds" in item

    # Channel info fields
    assert "channel_title" in item
    assert "channel_username" in item

    # Constructed field
    assert "message_link" in item

    # Verify values
    assert item["s3_object_name"] == "full-test.mp4"
    assert item["message_text"] == "Full test message"
    assert item["message_id"] == msg.id
    assert item["download_status"] == "Downloaded"
    assert item["file_extension"] == "mp4"
    assert item["file_size_bytes"] == 5242880
    assert item["file_duration_seconds"] == 180.0
    assert item["channel_title"] == "Full Channel"
    assert item["channel_username"] == "full_ch"
    assert item["download_retry_attempt"] == 1
    assert item["download_start_time"] is not None
    assert item["download_finished_time"] is not None


def test_downloads_null_optional_fields(telegram_client: TestClient) -> None:
    """Verify NULL optional fields are handled correctly."""
    _create_channel(channel_id=510, title="Nulls Channel", username="nulls_ch")
    msg = _create_message(
        channel_id=510,
        message_id=511,
        message_text="",
        status="HasFile",
        file_extension="",
        file_mime_type="",
        file_size_bytes=0,
        file_duration_seconds=0.0,
    )
    _create_download(
        message_id=msg.id,
        s3_object_name="minimal.mp4",
        download_queue_time=arrow.now().naive,
        download_start_time=None,
        download_finished_time=arrow.now().naive,
    )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    item = data[0]
    assert item["download_start_time"] is None
    assert item["message_text"] == ""
    assert item["file_extension"] == ""
    assert item["file_mime_type"] == ""
    assert item["file_size_bytes"] == 0


# ─── Message link construction ───────────────────────────────────────────────


def test_downloads_message_link_public_channel(telegram_client: TestClient) -> None:
    """Channel with username → link is https://t.me/{username}/{message_id}."""
    _create_channel(channel_id=600, title="Public Channel", username="public_ch")
    msg = _create_message(channel_id=600, message_id=601)
    _create_download(message_id=msg.id, s3_object_name="public.mp4")

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message_link"] == "https://t.me/public_ch/601"


def test_downloads_message_link_private_channel(telegram_client: TestClient) -> None:
    """Channel without username → link is https://t.me/c/{channel_id}/{message_id}."""
    _create_channel(channel_id=700, title="Private Channel", username=None)
    msg = _create_message(channel_id=700, message_id=701)
    _create_download(message_id=msg.id, s3_object_name="private.mp4")

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message_link"] == "https://t.me/c/700/701"


def test_downloads_message_link_multiple_channels(telegram_client: TestClient) -> None:
    """Mix of public and private channels produce correct links."""
    _create_channel(channel_id=800, title="Public", username="pub_ch")
    _create_channel(channel_id=801, title="Private", username=None)

    msg_pub = _create_message(channel_id=800, message_id=810)
    _create_download(message_id=msg_pub.id, s3_object_name="pub.mp4")

    msg_priv = _create_message(channel_id=801, message_id=811)
    _create_download(message_id=msg_priv.id, s3_object_name="priv.mp4")

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    links = {item["message_link"] for item in data}
    assert "https://t.me/pub_ch/810" in links
    assert "https://t.me/c/801/811" in links


# ─── Authentication ───────────────────────────────────────────────────────────


def test_downloads_auth_required() -> None:
    """Unauthenticated request returns 401/403."""
    from main import app

    with TestClient(app=app, raise_server_exceptions=False) as client:
        response = client.get("/telegram-browser/downloads")
        assert response.status_code in (401, 403)


# ─── Edge cases ───────────────────────────────────────────────────────────────


def test_downloads_unique_download_per_message_lifecycle(telegram_client: TestClient) -> None:
    """A message has at most one TelegramDownload: queueing after a terminal state replaces the old record."""
    _create_channel(channel_id=900, title="Multi Channel", username="multi_ch")
    msg = _create_message(channel_id=900, message_id=901, message_text="Lifecycle msg")

    # First queue creates a download record
    response = telegram_client.get(f"/telegram-browser/queue-file/{msg.id}")
    assert response.status_code == 200

    # Mark the download as terminal (Downloaded), then queue again: old record is replaced
    download = TelegramDownload.objects().where(TelegramDownload.message == msg.id).first().run_sync()
    assert download is not None
    download.status = DownloadStatus.Downloaded
    download.save().run_sync()

    response = telegram_client.get(f"/telegram-browser/queue-file/{msg.id}")
    assert response.status_code == 200

    # Unique FK on TelegramDownload.message: only one record survives, freshly Queued
    downloads = TelegramDownload.objects().where(TelegramDownload.message == msg.id).run_sync()
    assert len(downloads) == 1
    assert downloads[0].status == DownloadStatus.Queued


def test_downloads_boundary_exactly_7_days(telegram_client: TestClient) -> None:
    """Download finished just under 7 days ago is included; exactly 7+ days is excluded."""
    _create_channel(channel_id=910, title="Boundary Channel", username="boundary_ch")

    # Just under 7 days — should be included
    msg_in = _create_message(channel_id=910, message_id=911, message_text="Just inside")
    _create_download(
        message_id=msg_in.id,
        s3_object_name="inside.mp4",
        download_finished_time=arrow.now().shift(days=-6, hours=-23).naive,
    )

    # Just over 7 days — should be excluded
    msg_out = _create_message(channel_id=910, message_id=912, message_text="Just outside")
    _create_download(
        message_id=msg_out.id,
        s3_object_name="outside.mp4",
        download_finished_time=arrow.now().shift(days=-7, hours=-1).naive,
    )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["s3_object_name"] == "inside.mp4"


def test_downloads_limit_1000(telegram_client: TestClient) -> None:
    """Endpoint respects 1000 result limit (verify no crash with many records)."""
    _create_channel(channel_id=920, title="Limit Channel", username="limit_ch")

    # Create a few downloads - we can't easily create 1000+ in tests
    for i in range(5):
        msg = _create_message(channel_id=920, message_id=920 + i, message_text=f"Msg {i}")
        _create_download(
            message_id=msg.id,
            s3_object_name=f"file_{i}.mp4",
            download_queue_time=arrow.now().shift(hours=-i).naive,
            download_finished_time=arrow.now().shift(hours=-i).naive,
        )

    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
