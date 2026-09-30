"""Tests that the allowlist has no dotenv fallback via Settings."""

import os
from unittest.mock import patch

import pytest
from fastapi import HTTPException

from components.login.allowlist import parse_allowlist, require_allowed_user
from components.login.cookies import LoggedInUser
from settings import Settings, get_settings


def test_settings_default_empty_parses_to_empty_set(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    try:
        monkeypatch.delenv("ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER", raising=False)
        assert Settings.model_fields["allowed_twitch_users_for_telegram_browser"].default == ""
        settings = Settings(_env_file=None)
        assert settings.allowed_twitch_users_for_telegram_browser == ""
        assert parse_allowlist(settings.allowed_twitch_users_for_telegram_browser) == set()
    finally:
        get_settings.cache_clear()


@pytest.mark.asyncio
async def test_settings_reads_env_but_require_allowed_user_follows_environ_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    get_settings.cache_clear()
    try:
        monkeypatch.setenv("ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER", "alice twitch")
        settings = Settings()
        assert settings.allowed_twitch_users_for_telegram_browser == "alice twitch"
        assert parse_allowlist(settings.allowed_twitch_users_for_telegram_browser) == {"alice twitch"}
        with patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "bob github"}):
            assert settings.allowed_twitch_users_for_telegram_browser == "alice twitch"
            assert os.environ["ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER"] == "bob github"
            alice = LoggedInUser(id=1, name="alice", service="twitch")
            bob = LoggedInUser(id=2, name="bob", service="github")
            with pytest.raises(HTTPException) as exc_info:
                await require_allowed_user(current_user=alice)
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Access denied"
            assert await require_allowed_user(current_user=bob) is bob
        divergent = Settings(allowed_twitch_users_for_telegram_browser="alice twitch")
        with patch.dict(os.environ, {"ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER": "bob github"}):
            assert divergent.allowed_twitch_users_for_telegram_browser == "alice twitch"
            alice = LoggedInUser(id=1, name="alice", service="twitch")
            bob = LoggedInUser(id=2, name="bob", service="github")
            with pytest.raises(HTTPException) as exc_info:
                await require_allowed_user(current_user=alice)
            assert exc_info.value.status_code == 403
            assert exc_info.value.detail == "Access denied"
            assert await require_allowed_user(current_user=bob) is bob
    finally:
        get_settings.cache_clear()


def test_allowed_field_type_is_str(monkeypatch: pytest.MonkeyPatch) -> None:
    get_settings.cache_clear()
    try:
        monkeypatch.delenv("ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER", raising=False)
        assert Settings.model_fields["allowed_twitch_users_for_telegram_browser"].annotation is str
        settings = Settings(_env_file=None)
        assert isinstance(settings.allowed_twitch_users_for_telegram_browser, str)
        assert type(settings.allowed_twitch_users_for_telegram_browser) is str
    finally:
        get_settings.cache_clear()
