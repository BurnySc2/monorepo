"""Tests for GET /telegram-browser/channel-names endpoint."""

from datetime import datetime

from fastapi.testclient import TestClient

from models.telegram_browser import TelegramChannel

_TABLE = TelegramChannel._meta.tablename


def _create_channel(
    channel_id: int,
    title: str,
    username: str | None = None,
) -> None:
    """Create a TelegramChannel record. Uses raw SQL when username is None
    to bypass the DB NOT NULL constraint on channel_username."""
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
        # The DB column has NOT NULL from migration. Temporarily drop the constraint
        # to insert a NULL value. No need to restore - the test fixture drops and
        # recreates the table after each test.
        TelegramChannel.raw(f"ALTER TABLE {_TABLE} ALTER COLUMN channel_username DROP NOT NULL").run_sync()
        channel = TelegramChannel(
            channel_id=channel_id,
            channel_title=title,
            channel_username=None,
            creation_date=datetime(2024, 1, 1),
            participants=100,
            last_parsed=datetime(2024, 1, 1),
        )
        channel.save().run_sync()


# ─── Happy Path ───────────────────────────────────────────────────────────────


def test_channel_names_returns_list(telegram_client: TestClient) -> None:
    """Endpoint returns 200 with an empty list when no channels exist."""
    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_channel_names_with_usernames(telegram_client: TestClient) -> None:
    """Endpoint returns channels that have a channel_username set."""
    _create_channel(channel_id=1, title="First Channel", username="first")
    _create_channel(channel_id=2, title="Second Channel", username="second")

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

    titles = {item["channel_title"] for item in data}
    assert titles == {"First Channel", "Second Channel"}

    for item in data:
        assert "channel_title" in item
        assert "channel_username" in item
        assert isinstance(item["channel_title"], str)
        assert isinstance(item["channel_username"], str)


# ─── Filtering: null usernames excluded ──────────────────────────────────────


def test_channel_names_excludes_null_usernames(telegram_client: TestClient) -> None:
    """Channels with null channel_username are excluded from results."""
    _create_channel(channel_id=1, title="With Username", username="myuser")
    _create_channel(channel_id=2, title="No Username", username=None)

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["channel_title"] == "With Username"
    assert data[0]["channel_username"] == "myuser"


def test_channel_names_all_null_usernames(telegram_client: TestClient) -> None:
    """When all channels have null channel_username, response is an empty list."""
    _create_channel(channel_id=1, title="Channel A", username=None)
    _create_channel(channel_id=2, title="Channel B", username=None)
    _create_channel(channel_id=3, title="Channel C", username=None)

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    assert data == []


# ─── Ordering ─────────────────────────────────────────────────────────────────


def test_channel_names_ordered_alphabetically(telegram_client: TestClient) -> None:
    """Results are sorted alphabetically by channel_title."""
    _create_channel(channel_id=1, title="Zebra Channel", username="zebra")
    _create_channel(channel_id=2, title="Apple Channel", username="apple")
    _create_channel(channel_id=3, title="Mango Channel", username="mango")

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3

    titles = [item["channel_title"] for item in data]
    assert titles == sorted(titles)


def test_channel_names_ordering_ignores_username(telegram_client: TestClient) -> None:
    """Ordering is by title, not by username."""
    _create_channel(channel_id=1, title="C Channel", username="zzz")
    _create_channel(channel_id=2, title="A Channel", username="aaa")
    _create_channel(channel_id=3, title="B Channel", username="bbb")

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    titles = [item["channel_title"] for item in data]
    assert titles == ["A Channel", "B Channel", "C Channel"]


# ─── Authentication ───────────────────────────────────────────────────────────


def test_channel_names_requires_auth() -> None:
    """Endpoint returns 403 when called without authentication."""
    from main import app

    # Use a fresh client without dependency override for auth
    with TestClient(app=app, raise_server_exceptions=False) as client:
        response = client.get("/telegram-browser/channel-names")
        assert response.status_code in (401, 403)


# ─── Response schema shape ───────────────────────────────────────────────────


def test_channel_names_response_shape(telegram_client: TestClient) -> None:
    """Each item in response matches the ChannelNameItem schema shape."""
    _create_channel(channel_id=1, title="My Title", username="myuser")

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1

    item = data[0]
    assert item == {"channel_title": "My Title", "channel_username": "myuser"}
    assert len(item) == 2  # Only the two expected keys


# ─── Edge cases ───────────────────────────────────────────────────────────────


def test_channel_names_single_channel(telegram_client: TestClient) -> None:
    """Single channel with username is returned correctly."""
    _create_channel(channel_id=1, title="Only Channel", username="solo")

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0] == {"channel_title": "Only Channel", "channel_username": "solo"}


def test_channel_names_special_characters_in_title(telegram_client: TestClient) -> None:
    """Titles with special characters are returned as-is."""
    _create_channel(channel_id=1, title="🎉 Emoji Channel!", username="emoji_ch")
    _create_channel(channel_id=2, title="Channel with spaces & symbols @#$", username="special")

    response = telegram_client.get("/telegram-browser/channel-names")
    assert response.status_code == 200
    data = response.json()
    titles = [item["channel_title"] for item in data]
    assert "🎉 Emoji Channel!" in titles
    assert "Channel with spaces & symbols @#$" in titles
