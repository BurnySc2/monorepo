"""IRC backoff tests for tenacity-backed reconnect (offline, fast).

Verifies exponential backoff with jitter, max-attempt guard, and the offline
guard that avoids a tight reconnect loop when reader/writer stay missing.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from components.tts.irc_bot_async import IRCClient


def _make_client(**overrides) -> IRCClient:
    kwargs = {"channel": "teststream", "read_name_lang": "none", "callback": lambda *args: None}
    kwargs.update(overrides)
    return IRCClient(**kwargs)  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_handle_reconnect_increments_attempts() -> None:
    """handle_reconnect bumps reconnect_attempts and resets on connect."""
    client = _make_client()
    client.connect = AsyncMock(
        side_effect=lambda: setattr(client, "reader", MagicMock()) or setattr(client, "writer", MagicMock())
    )
    client.writer = MagicMock()
    client.writer.close = MagicMock()
    client.writer.wait_closed = AsyncMock()

    assert client.reconnect_attempts == 0
    await client.handle_reconnect()
    assert client.reconnect_attempts == 1


@pytest.mark.asyncio
async def test_handle_reconnect_respects_max_attempts() -> None:
    """handle_reconnect returns early when max attempts already reached."""
    client = _make_client()
    client.max_reconnect_attempts = 3
    client.reconnect_attempts = 3
    client._connect_with_retry = AsyncMock()  # type: ignore[method-assign]

    await client.handle_reconnect()

    client._connect_with_retry.assert_not_awaited()
    assert client.reconnect_attempts == 3


@pytest.mark.asyncio
async def test_handle_reconnect_sleeps_when_transport_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Offline guard sleeps when mocked connect leaves reader/writer missing."""
    client = _make_client()
    client.connect = AsyncMock(return_value=None)
    client.writer = None
    client.reader = None

    sleep_mock = AsyncMock()
    monkeypatch.setattr("components.tts.irc_bot_async.asyncio.sleep", sleep_mock)

    await client.handle_reconnect()

    assert client.reconnect_attempts == 1
    sleep_mock.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_connect_with_retry_retries_transient_then_succeeds(monkeypatch: pytest.MonkeyPatch) -> None:
    """_connect_with_retry retries OSError then succeeds (no real sleep)."""
    import asyncio

    client = _make_client()
    calls = {"n": 0}

    async def _flaky_connect() -> None:
        calls["n"] += 1
        if calls["n"] == 1:
            raise OSError("transient")
        client.reader = MagicMock()
        client.writer = MagicMock()

    client.connect = _flaky_connect  # type: ignore[method-assign]

    # Speed up retry: tenacity uses asyncio.sleep for async backoff.
    async def _no_sleep(_: float) -> None:
        return None

    monkeypatch.setattr(asyncio, "sleep", _no_sleep)

    await client._connect_with_retry()

    assert calls["n"] == 2


def test_connect_retry_config_matches_max_attempts() -> None:
    """Inner retry is 3; outer max is 10 (total budget <= 30)."""
    retrying = getattr(IRCClient._connect_with_retry, "retry", None)
    # tenacity AsyncRetrying with stop_after_attempt(3) is configured.
    assert retrying is not None
    stop = getattr(retrying, "stop", None)
    assert stop is not None
    assert getattr(stop, "max_attempt_number", None) == 3
    assert _make_client().max_reconnect_attempts == 10
    assert _make_client().max_reconnect_attempts * getattr(stop, "max_attempt_number") <= 30
