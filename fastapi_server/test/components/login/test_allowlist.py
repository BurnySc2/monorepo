"""Tests for the allowlist dependency."""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from components.login.allowlist import parse_allowlist, require_allowed_user
from components.login.cookies import LoggedInUser

# ─── parse_allowlist (pure function) ─────────────────────────────────────────


class TestParseAllowlist:
    def test_empty_string(self) -> None:
        assert parse_allowlist("") == set()

    def test_none(self) -> None:
        assert parse_allowlist(None) == set()

    def test_single_entry(self) -> None:
        assert parse_allowlist("burnysc2 twitch") == {"burnysc2 twitch"}

    def test_multiple_entries(self) -> None:
        result = parse_allowlist("burnysc2 twitch;other_user github")
        assert result == {"burnysc2 twitch", "other_user github"}

    def test_strips_whitespace(self) -> None:
        result = parse_allowlist("  burnysc2 twitch  ;  other_user github  ")
        assert result == {"burnysc2 twitch", "other_user github"}

    def test_filters_empty_entries(self) -> None:
        result = parse_allowlist("burnysc2 twitch;; ;other_user github")
        assert result == {"burnysc2 twitch", "other_user github"}

    def test_lowercases(self) -> None:
        result = parse_allowlist("Burnysc2 Twitch")
        assert result == {"burnysc2 twitch"}

    def test_only_empty_entries(self) -> None:
        assert parse_allowlist(" ; ; ") == set()


# ─── require_allowed_user (FastAPI dependency) ───────────────────────────────


@pytest.mark.asyncio
async def test_allowed_user_passes() -> None:
    user = LoggedInUser(id=1, name="burnysc2", service="twitch")
    with patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "burnysc2 twitch"}):
        result = await require_allowed_user(current_user=user)
    assert result is user


@pytest.mark.asyncio
async def test_denied_user_raises_403() -> None:
    user = LoggedInUser(id=2, name="intruder", service="github")
    with (
        patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "burnysc2 twitch"}),
        pytest.raises(HTTPException) as exc_info,
    ):
        await require_allowed_user(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_empty_env_var_denies_all() -> None:
    user = LoggedInUser(id=1, name="burnysc2", service="twitch")
    with (
        patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": ""}, clear=False),
        pytest.raises(HTTPException) as exc_info,
    ):
        await require_allowed_user(current_user=user)
    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
async def test_unset_env_var_denies_all() -> None:
    user = LoggedInUser(id=1, name="burnysc2", service="twitch")
    env = {k: v for k, v in os.environ.items() if k != "ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER"}
    with (
        patch.dict(os.environ, env, clear=True),
        pytest.raises(HTTPException) as exc_info,
    ):
        await require_allowed_user(current_user=user)
    assert exc_info.value.status_code == 403
