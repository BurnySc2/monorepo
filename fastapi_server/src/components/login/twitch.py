from __future__ import annotations

from typing import Literal

import httpx

from components.login.cookies import (
    BACKEND_SERVER_URL,
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
)


async def twitch_verify_code(code: str) -> str | Literal[503, 409]:
    async with httpx.AsyncClient() as client:
        post_response = await client.post(
            "https://id.twitch.tv/oauth2/token",
            headers={"Accept": "application/json"},
            json={
                "client_id": TWITCH_CLIENT_ID,
                "client_secret": TWITCH_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{BACKEND_SERVER_URL}/login/twitch",
            },
        )
        if post_response.is_error:
            return 503
        data: dict[str, str] = post_response.json()
    if "error" in data:
        return 409
    return data["access_token"]
