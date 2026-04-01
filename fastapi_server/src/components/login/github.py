from __future__ import annotations

from typing import Literal

import httpx

from components.login.cookies import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
)


async def github_verify_code(code: str) -> str | Literal[503, 409]:
    async with httpx.AsyncClient() as client:
        post_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            json={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )
        if post_response.is_error:
            return 503
        data: dict[str, str] = post_response.json()
    if "error" in data:
        return 409
    return data["access_token"]
