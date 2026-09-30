"""Offline tests for login OAuth provider registry."""

from __future__ import annotations

import dataclasses

import pytest

from components.login.cookies import COOKIES
from components.login.providers import PROVIDERS, OAuthProvider, _require_env


class TestProvidersDict:
    def test_has_expected_providers(self):
        assert set(PROVIDERS) == {"twitch", "github", "google"}

    @pytest.mark.parametrize("name", ["twitch", "github", "google"])
    def test_provider_fields(self, name: str):
        provider = PROVIDERS[name]
        assert isinstance(provider, OAuthProvider)
        assert provider.name == name
        assert provider.cookie_key == COOKIES[name]
        assert provider.authorize_url.startswith("https://")
        assert provider.scope
        # OAuth client IDs default to None (configured via environment); must be str when set.
        assert provider.client_id is None or isinstance(provider.client_id, str)
        assert provider.redirect_path == f"/login/{name}"
        assert callable(provider.get_user)
        assert callable(provider.verify_code)

    def test_twitch_values(self):
        provider = PROVIDERS["twitch"]
        assert "twitch.tv" in provider.authorize_url
        assert provider.scope == "user:read:email"

    def test_github_values(self):
        provider = PROVIDERS["github"]
        assert "github.com" in provider.authorize_url
        assert provider.scope == "read:user"

    def test_google_values(self):
        provider = PROVIDERS["google"]
        assert "google.com" in provider.authorize_url
        assert provider.scope == "profile"

    def test_provider_is_frozen(self):
        provider = PROVIDERS["twitch"]
        with pytest.raises(dataclasses.FrozenInstanceError):
            provider.name = "other"  # type: ignore[misc]


class TestRequireEnv:
    def test_returns_value_when_set(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.setenv("CHUNK2_TEST_ENV_VAR", "hello")
        assert _require_env("CHUNK2_TEST_ENV_VAR") == "hello"

    def test_returns_none_when_missing_in_dev(self, monkeypatch: pytest.MonkeyPatch):
        monkeypatch.delenv("CHUNK2_TEST_ENV_VAR_MISSING", raising=False)
        monkeypatch.setenv("STAGE", "dev")
        assert _require_env("CHUNK2_TEST_ENV_VAR_MISSING") is None

    def test_warns_in_prod_when_missing(self, monkeypatch: pytest.MonkeyPatch):
        # Uses loguru, not stdlib logging: just assert it still returns None
        # without raising, even in prod.
        monkeypatch.delenv("CHUNK2_TEST_ENV_VAR_MISSING", raising=False)
        monkeypatch.setenv("STAGE", "prod")
        assert _require_env("CHUNK2_TEST_ENV_VAR_MISSING") is None
