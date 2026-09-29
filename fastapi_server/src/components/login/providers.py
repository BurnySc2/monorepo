"""OAuth provider registry for login routes.

Consolidates per-provider configuration (Twitch, GitHub, Google) so
``routes/login.py`` can delegate to shared helpers instead of duplicating
callback/start logic per provider.
"""

from __future__ import annotations

import os
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from loguru import logger

from components.login.cookies import (
    COOKIES,
    GITHUB_CLIENT_ID,
    GOOGLE_CLIENT_ID,
    TWITCH_CLIENT_ID,
    github_get_user,
    google_get_user,
    twitch_get_user,
)
from components.login.github import github_verify_code
from components.login.google import google_verify_code
from components.login.twitch import twitch_verify_code


def _require_env(name: str) -> str | None:
    """Return ``os.getenv(name)``, warning in non-dev stages when missing.

    In production (``STAGE`` anything other than ``dev``/unset/``test``) a
    missing variable is almost certainly a misconfiguration, so emit a
    ``loguru`` warning while still returning ``None`` to keep local-dev
    defaults working.
    """
    value = os.getenv(name)
    if not value and os.getenv("STAGE", "dev") not in ("dev", "test", ""):
        logger.warning(f"Missing required environment variable {name!r} in non-dev STAGE")
    return value


@dataclass(frozen=True)
class OAuthProvider:
    """Immutable per-provider OAuth configuration."""

    name: str
    cookie_key: str
    get_user: Callable[[str | None], Awaitable[Any]]
    verify_code: Callable[[str], Awaitable[Any]]
    authorize_url: str
    scope: str
    client_id: str
    redirect_path: str


PROVIDERS: dict[str, OAuthProvider] = {
    "twitch": OAuthProvider(
        name="twitch",
        cookie_key=COOKIES["twitch"],
        get_user=twitch_get_user,
        verify_code=twitch_verify_code,
        authorize_url="https://id.twitch.tv/oauth2/authorize",
        scope="user:read:email",
        client_id=TWITCH_CLIENT_ID,
        redirect_path="/login/twitch",
    ),
    "github": OAuthProvider(
        name="github",
        cookie_key=COOKIES["github"],
        get_user=github_get_user,
        verify_code=github_verify_code,
        authorize_url="https://github.com/login/oauth/authorize",
        scope="read:user",
        client_id=GITHUB_CLIENT_ID,
        redirect_path="/login/github",
    ),
    "google": OAuthProvider(
        name="google",
        cookie_key=COOKIES["google"],
        get_user=google_get_user,
        verify_code=google_verify_code,
        authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
        scope="profile",
        client_id=GOOGLE_CLIENT_ID,
        redirect_path="/login/google",
    ),
}


__all__ = ["OAuthProvider", "PROVIDERS", "_require_env"]
