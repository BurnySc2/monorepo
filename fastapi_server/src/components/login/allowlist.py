from __future__ import annotations

import os
from typing import Annotated

from fastapi import Depends, HTTPException

from components.login.cookies import LoggedInUser, get_current_user


def parse_allowlist(env_value: str | None) -> set[str]:
    """Parse a semicolon-delimited allowlist from an env var value.

    Returns a set of lowercase, stripped strings. Empty/unset → empty set (fail-closed).
    Entries without content after stripping are filtered out.
    """
    if not env_value:
        return set()
    return {entry.strip().lower() for entry in env_value.split(";") if entry.strip()}


async def require_allowed_user(
    current_user: Annotated[LoggedInUser, Depends(get_current_user)],
) -> LoggedInUser:
    """FastAPI dependency that restricts access to users on an allowlist.

    Reads ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER per-request.
    Empty/unset env var → deny all (fail-closed).
    """
    env_value = os.getenv("ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER")
    allowed = parse_allowlist(env_value)

    if current_user.db_name.lower() not in allowed:
        raise HTTPException(status_code=403, detail="Access denied")

    return current_user
