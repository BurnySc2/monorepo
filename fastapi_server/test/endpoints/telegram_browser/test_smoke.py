"""Smoke tests for telegram browser endpoints."""

from datetime import datetime

from fastapi.testclient import TestClient


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


def test_delete_file_not_found(telegram_client: TestClient) -> None:
    """Delete file returns 404 for non-existent message."""
    response = telegram_client.delete("/telegram-browser/delete-file/99999")
    assert response.status_code == 404


def test_view_file_not_found(telegram_client: TestClient) -> None:
    """View file returns 404 for non-existent message."""
    response = telegram_client.get("/telegram-browser/view-file/99999")
    assert response.status_code == 404


def test_download_file_not_found(telegram_client: TestClient) -> None:
    """Download file returns 404 for non-existent message."""
    response = telegram_client.get("/telegram-browser/download-file/99999", follow_redirects=False)
    assert response.status_code == 404


def test_search_with_data(telegram_client: TestClient) -> None:
    """Search returns data when messages exist."""
    from models.telegram_browser import TelegramChannel, TelegramMessage

    # Create a channel
    channel = TelegramChannel(
        channel_id=123456,
        channel_title="Test Channel",
        channel_username="testchannel",
        creation_date=datetime.now(),
        participants=100,
        last_parsed=datetime.now(),
    )
    channel.save().run_sync()

    # Create a message
    message = TelegramMessage(
        message_id=789,
        message_date=datetime.now(),
        message_text="Hello world",
        amount_of_reactions=5,
        amount_of_comments=2,
        status="HasFile",
        channel=channel.id,
    )
    message.save().run_sync()

    # Search should return the message
    response = telegram_client.get("/telegram-browser/search")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["message_text"] == "Hello world"
    assert data[0]["channel_title"] == "Test Channel"
    assert data[0]["metadata"]["status"] == "HasFile"
    assert data[0]["channel_username"] == "testchannel"
