from __future__ import annotations

from typing import Literal

import httpx

from rio_app.components.login.cookies import (
    BACKEND_SERVER_URL,
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    TwitchUser,
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


async def twitch_get_user(twitch_access_token: str | None) -> TwitchUser | None:
    if twitch_access_token is None:
        return None
    async with httpx.AsyncClient() as client:
        # https://dev.twitch.tv/docs/api/reference/#get-users
        get_response = await client.get(
            url="https://api.twitch.tv/helix/users",
            headers={
                "Authorization": f"Bearer {twitch_access_token}",
                "Client-Id": TWITCH_CLIENT_ID,
                "Accept": "application/json",
            },
        )
        if get_response.is_error:
            return None
        data = get_response.json()["data"][0]
    twitch_user = TwitchUser(
        id=int(data["id"]),
        login=data["login"],
        display_name=data["display_name"],
        email="",
        # email=response_json["email"],
    )
    return twitch_user
