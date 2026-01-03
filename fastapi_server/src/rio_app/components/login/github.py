from __future__ import annotations

from typing import Literal

import httpx

from rio_app.components.login.cookies import (
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    GithubUser,
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


async def github_get_user(github_access_token: str | None) -> GithubUser | None:
    if github_access_token is None:
        return None
    async with httpx.AsyncClient() as client:
        # https://dev.twitch.tv/docs/api/reference/#get-users
        get_response = await client.get(
            "https://api.github.com/user",
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "Authorization": f"Bearer {github_access_token}",
            },
        )
        if get_response.is_error:
            return None
        data = get_response.json()
    github_user = GithubUser(
        id=data["id"],
        login=data["login"],
    )
    return github_user
