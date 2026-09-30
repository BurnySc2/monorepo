"""Tests for the allowlist dependency."""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from components.login.allowlist import parse_allowlist, require_allowed_user
from components.login.cookies import LoggedInUser

# --- parse_allowlist: pure function ---


@pytest.mark.parametrize(
    ("raw", "want"),
    [
        ("", set()),
        (None, set()),
        ("burnysc2 twitch", {"burnysc2 twitch"}),
        ("burnysc2 twitch;other_user github", {"burnysc2 twitch", "other_user github"}),
        ("  burnysc2 twitch  ;  other_user github  ", {"burnysc2 twitch", "other_user github"}),
        ("burnysc2 twitch;; ;other_user github", {"burnysc2 twitch", "other_user github"}),
        ("Burnysc2 Twitch", {"burnysc2 twitch"}),
        (" ; ; ", set()),
    ],
)
def test_parse_allowlist(raw: str | None, want: set[str]) -> None:
    assert parse_allowlist(raw) == want


# --- require_allowed_user: FastAPI dependency ---


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
    assert exc_info.value.detail == "Access denied"


@pytest.mark.asyncio
async def test_empty_env_var_denies_all() -> None:
    user = LoggedInUser(id=1, name="burnysc2", service="twitch")
    with (
        patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": ""}, clear=False),
        pytest.raises(HTTPException) as exc_info,
    ):
        await require_allowed_user(current_user=user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied"


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
    assert exc_info.value.detail == "Access denied"


# --- Env handling: case / multi / whitespace / empty-vs-unset ---


@pytest.mark.asyncio
async def test_case_insensitive_match() -> None:
    user = LoggedInUser(id=1, name="BurnySC2", service="twitch")
    with patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "BURNYSC2 TWITCH"}):
        result = await require_allowed_user(current_user=user)
    assert result is user


@pytest.mark.asyncio
async def test_semicolon_multi_allows_each_entry() -> None:
    alice = LoggedInUser(id=1, name="burnysc2", service="twitch")
    bob = LoggedInUser(id=2, name="other_user", service="github")
    with patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "burnysc2 twitch;other_user github"}):
        assert await require_allowed_user(current_user=alice) is alice
        assert await require_allowed_user(current_user=bob) is bob


@pytest.mark.asyncio
async def test_whitespace_trim_match() -> None:
    user = LoggedInUser(id=1, name="burnysc2", service="twitch")
    with patch.dict(
        os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "  burnysc2 twitch  ;  other_user github  "}
    ):
        result = await require_allowed_user(current_user=user)
    assert result is user


@pytest.mark.asyncio
@pytest.mark.parametrize("setup", ["empty", "unset"])
async def test_empty_vs_unset_both_deny(setup: str) -> None:
    user = LoggedInUser(id=1, name="burnysc2", service="twitch")
    if setup == "empty":
        ctx = patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": ""}, clear=False)
    else:
        env = {k: v for k, v in os.environ.items() if k != "ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER"}
        ctx = patch.dict(os.environ, env, clear=True)
    with ctx, pytest.raises(HTTPException) as exc_info:
        await require_allowed_user(current_user=user)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "Access denied"


# --- Per-request reload: no reimport, no cache ---


@pytest.mark.asyncio
async def test_allowlist_reloads_per_request_without_reimport() -> None:
    user_a = LoggedInUser(id=1, name="burnysc2", service="twitch")
    user_b = LoggedInUser(id=2, name="other_user", service="github")
    with patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "burnysc2 twitch"}):
        assert await require_allowed_user(current_user=user_a) is user_a
    with patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "other_user github"}):
        with pytest.raises(HTTPException) as exc_info:
            await require_allowed_user(current_user=user_a)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail == "Access denied"
        assert await require_allowed_user(current_user=user_b) is user_b
