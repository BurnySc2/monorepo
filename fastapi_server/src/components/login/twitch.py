from __future__ import annotations

from typing import Literal

import httpx

from settings import settings


async def twitch_verify_code(code: str) -> str | Literal[503, 409]:
    async with httpx.AsyncClient() as client:
        post_response = await client.post(
            "https://id.twitch.tv/oauth2/token",
            headers={"Accept": "application/json"},
            json={
                "client_id": settings.twitch_app_client_id,
                "client_secret": settings.twitch_app_client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{settings.backend_server_url}/login/twitch",
            },
        )
        if post_response.is_error:
            return 503
        data: dict[str, str] = post_response.json()
    if "error" in data:
        return 409
    return data["access_token"]
