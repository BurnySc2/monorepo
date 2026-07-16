"""Smoke tests for telegram browser endpoints."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import arrow
from fastapi.testclient import TestClient

from models.telegram_browser import TelegramChannel, TelegramDownload, TelegramMessage


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
        TelegramChannel.raw(
            f"ALTER TABLE {TelegramChannel._meta.tablename} ALTER COLUMN channel_username DROP NOT NULL"
        ).run_sync()
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
    status: str = "Downloaded",
    file_extension: str = "mp4",
    file_mime_type: str = "video/mp4",
) -> TelegramMessage:
    """Create a TelegramMessage record."""
    message = TelegramMessage(
        channel=channel_id,
        message_id=message_id,
        message_date=datetime(2024, 6, 15),
        message_text="Test message",
        amount_of_reactions=0,
        amount_of_comments=0,
        status=status,
        file_extension=file_extension,
        file_mime_type=file_mime_type,
    )
    message.save().run_sync()
    return message


def _create_download(
    message_id: int,
    s3_object_name: str = "test-file.mp4",
) -> TelegramDownload:
    """Create a TelegramDownload record."""
    download = TelegramDownload(
        message=message_id,
        download_queue_time=arrow.now().naive,
        download_start_time=arrow.now().naive,
        download_finished_time=arrow.now().naive,
        download_retry_attempt=0,
        s3_object_name=s3_object_name,
    )
    download.save().run_sync()
    return download


# ─── Existing smoke tests ────────────────────────────────────────────────────


def test_search_returns_200_empty(telegram_client: TestClient) -> None:
    """Search endpoint returns 200 with empty results when no messages exist."""
    response = telegram_client.get("/telegram-browser/search")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_search_with_filters_returns_200(telegram_client: TestClient) -> None:
    """Search endpoint accepts all filter parameters."""
    params = {
        "search_text": "test",
        "channel_name": "channel",
        "datetime_min": "2024-01-01T00:00:00",
        "datetime_max": "2024-12-31T23:59:59",
        "reactions_min": 0,
        "reactions_max": 100,
        "comments_min": 0,
        "comments_max": 50,
        "must_have_file": False,
        "file_extension": "mp4",
        "file_duration_min": "00:00:00",
        "file_duration_max": "01:00:00",
        "file_size_min": 0,
        "file_size_max": 100,
        "file_image_width_min": 0,
        "file_image_width_max": 1920,
        "file_image_height_min": 0,
        "file_image_height_max": 1080,
    }
    response = telegram_client.get("/telegram-browser/search", params=params)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_queue_file_not_found(telegram_client: TestClient) -> None:
    """Queue file returns 404 for non-existent message."""
    response = telegram_client.get("/telegram-browser/queue-file/99999")
    assert response.status_code == 404


def test_search_with_data(telegram_client: TestClient) -> None:
    """Search returns data when messages exist."""
    _create_channel(channel_id=123456, title="Test Channel", username="testchannel")
    _create_message(channel_id=123456, message_id=789, status="HasFile")

    response = telegram_client.get("/telegram-browser/search")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message_text"] == "Test message"
    assert data[0]["channel_title"] == "Test Channel"
    assert data[0]["metadata"]["status"] == "HasFile"
    assert data[0]["channel_username"] == "testchannel"


# ─── DELETE /delete-file/{id} ────────────────────────────────────────────────


def test_delete_file_not_found(telegram_client: TestClient) -> None:
    """Delete file returns 404 for non-existent message."""
    response = telegram_client.delete("/telegram-browser/delete-file/99999")
    assert response.status_code == 404


@patch("routes.telegram_browser.get_s3_client")
def test_delete_file_success(mock_get_s3: MagicMock, telegram_client: TestClient) -> None:
    """DELETE /delete-file/{id} with valid download → deletes S3 object and DB record."""
    _create_channel(channel_id=1000, title="Del Channel", username="del_ch")
    msg = _create_message(channel_id=1000, message_id=1001, status="Downloaded")
    _create_download(message_id=msg.id, s3_object_name="to-delete.mp4")

    # Mock S3 client context manager
    mock_s3_client = AsyncMock()
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_s3_client)
    mock_context.__aexit__ = AsyncMock(return_value=False)
    mock_get_s3.return_value = mock_context

    response = telegram_client.delete(f"/telegram-browser/delete-file/{msg.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True

    # Verify message status was reset to HasFile
    updated_msg = TelegramMessage.objects().where(TelegramMessage.id == msg.id).first().run_sync()
    assert updated_msg is not None
    assert updated_msg.status == "HasFile"

    # Verify download record was removed
    download = TelegramDownload.objects().where(TelegramDownload.message == msg.id).first().run_sync()
    assert download is None


@patch("routes.telegram_browser.get_s3_client")
def test_delete_file_without_s3_object(mock_get_s3: MagicMock, telegram_client: TestClient) -> None:
    """DELETE /delete-file/{id} with no s3_object_name → still deletes DB record."""
    _create_channel(channel_id=1010, title="No S3 Channel", username="nos3_ch")
    msg = _create_message(channel_id=1010, message_id=1011, status="Downloaded")

    # Create download with empty s3_object_name
    download = TelegramDownload(
        message=msg.id,
        download_queue_time=arrow.now().naive,
        download_finished_time=arrow.now().naive,
        s3_object_name="",
    )
    download.save().run_sync()

    response = telegram_client.delete(f"/telegram-browser/delete-file/{msg.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["deleted"] is True

    # S3 client should NOT have been called (no object to delete)
    mock_get_s3.assert_not_called()


# ─── GET /view-file/{id} ─────────────────────────────────────────────────────


def test_view_file_not_found(telegram_client: TestClient) -> None:
    """View file returns 404 for non-existent message."""
    response = telegram_client.get("/telegram-browser/view-file/99999")
    assert response.status_code == 404


def test_view_file_not_downloaded(telegram_client: TestClient) -> None:
    """View file returns 400 when message status is not 'Downloaded'."""
    _create_channel(channel_id=2000, title="Not DL Channel", username="notdl_ch")
    msg = _create_message(channel_id=2000, message_id=2001, status="HasFile")

    response = telegram_client.get(f"/telegram-browser/view-file/{msg.id}")
    assert response.status_code == 400


def test_view_file_no_download_record(telegram_client: TestClient) -> None:
    """View file returns 400 when no download record exists."""
    _create_channel(channel_id=2010, title="No DL Record", username="nodelrec_ch")
    msg = _create_message(channel_id=2010, message_id=2011, status="Downloaded")

    response = telegram_client.get(f"/telegram-browser/view-file/{msg.id}")
    assert response.status_code == 400


@patch("routes.telegram_browser.get_s3_client")
def test_view_file_success(mock_get_s3: MagicMock, telegram_client: TestClient) -> None:
    """GET /view-file/{id} with valid download → returns presigned URL."""
    _create_channel(channel_id=2020, title="View Channel", username="view_ch")
    msg = _create_message(channel_id=2020, message_id=2021, status="Downloaded")
    _create_download(message_id=msg.id, s3_object_name="view-file.mp4")

    # Mock S3 client
    mock_s3_client = AsyncMock()
    mock_s3_client.head_object = AsyncMock(return_value={})
    mock_s3_client.generate_presigned_url = AsyncMock(return_value="https://presigned.example.com/view-file.mp4")
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_s3_client)
    mock_context.__aexit__ = AsyncMock(return_value=False)
    mock_get_s3.return_value = mock_context

    response = telegram_client.get(f"/telegram-browser/view-file/{msg.id}")
    assert response.status_code == 200
    data = response.json()
    assert "minio_url" in data
    assert "mime_type" in data
    assert data["minio_url"] == "https://presigned.example.com/view-file.mp4"
    assert data["mime_type"] == "video/mp4"


# ─── GET /download-file/{id} ─────────────────────────────────────────────────


def test_download_file_not_found(telegram_client: TestClient) -> None:
    """Download file returns 404 for non-existent message."""
    response = telegram_client.get("/telegram-browser/download-file/99999", follow_redirects=False)
    assert response.status_code == 404


def test_download_file_not_downloaded(telegram_client: TestClient) -> None:
    """Download file returns 400 when message status is not 'Downloaded'."""
    _create_channel(channel_id=3000, title="Not DL2 Channel", username="notdl2_ch")
    msg = _create_message(channel_id=3000, message_id=3001, status="Queued")

    response = telegram_client.get(f"/telegram-browser/download-file/{msg.id}", follow_redirects=False)
    assert response.status_code == 400


@patch("routes.telegram_browser.get_s3_client")
def test_download_file_success(mock_get_s3: MagicMock, telegram_client: TestClient) -> None:
    """GET /download-file/{id} with valid download → redirects to presigned URL."""
    _create_channel(channel_id=3020, title="DL Channel", username="dl_ch")
    msg = _create_message(channel_id=3020, message_id=3021, status="Downloaded")
    _create_download(message_id=msg.id, s3_object_name="download-file.mp4")

    # Mock S3 client
    mock_s3_client = AsyncMock()
    mock_s3_client.head_object = AsyncMock(return_value={})
    mock_s3_client.generate_presigned_url = AsyncMock(return_value="https://presigned.example.com/download-file.mp4")
    mock_context = AsyncMock()
    mock_context.__aenter__ = AsyncMock(return_value=mock_s3_client)
    mock_context.__aexit__ = AsyncMock(return_value=False)
    mock_get_s3.return_value = mock_context

    response = telegram_client.get(f"/telegram-browser/download-file/{msg.id}", follow_redirects=False)
    assert response.status_code == 302
    assert response.headers["location"] == "https://presigned.example.com/download-file.mp4"


@patch("routes.telegram_browser.get_s3_client")
def test_download_file_no_s3_object(mock_get_s3: MagicMock, telegram_client: TestClient) -> None:
    """Download file returns 400 when s3_object_name is empty."""
    _create_channel(channel_id=3030, title="Empty S3 Channel", username="emptys3_ch")
    msg = _create_message(channel_id=3030, message_id=3031, status="Downloaded")

    download = TelegramDownload(
        message=msg.id,
        download_queue_time=arrow.now().naive,
        download_finished_time=arrow.now().naive,
        s3_object_name="",
    )
    download.save().run_sync()

    response = telegram_client.get(f"/telegram-browser/download-file/{msg.id}", follow_redirects=False)
    assert response.status_code == 400


# ─── GET /downloads (basic smoke) ────────────────────────────────────────────


def test_downloads_returns_200_empty(telegram_client: TestClient) -> None:
    """Downloads endpoint returns 200 with empty list when no downloads exist."""
    response = telegram_client.get("/telegram-browser/downloads")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_downloads_auth_required() -> None:
    """Downloads endpoint returns 401/403 when called without authentication."""
    from main import app

    with TestClient(app=app, raise_server_exceptions=False) as client:
        response = client.get("/telegram-browser/downloads")
        assert response.status_code in (401, 403)
