from __future__ import annotations

from typing import Literal

import httpx

from components.login.cookies import (
    BACKEND_SERVER_URL,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
)


async def google_verify_code(code: str) -> str | Literal[503, 409]:
    async with httpx.AsyncClient() as client:
        post_response = await client.post(
            "https://oauth2.googleapis.com/token",
            headers={"Accept": "application/json"},
            json={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": f"{BACKEND_SERVER_URL}/login/google",
            },
        )
        if post_response.is_error:
            return 503
        data: dict[str, str] = post_response.json()
    if "error" in data:
        return 409
    return data["access_token"]
