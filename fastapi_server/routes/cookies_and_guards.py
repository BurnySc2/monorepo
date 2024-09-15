from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from typing import Annotated, Literal

import httpx
from dotenv import load_dotenv
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.params import Parameter
from litestar.stores.memory import MemoryStore

from prisma import Prisma
from routes.audiobook.schema import (
    AudioSettings,
)
from routes.audiobook.temp_generate_tts import get_supported_voices

load_dotenv()


# Github app for local development
GITHUB_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "2aab3b1a609cb1a4126c7eec121bad2343332113")

# Twitch app for local development
TWITCH_CLIENT_ID = os.getenv("TWITCH_APP_CLIENT_ID", "ddgeuklh32bi15odtfc0o7gu4g4ehn")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_APP_CLIENT_SECRET", "mtu72a2v35p8x7f4fddwmzc2wwdruu")

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "http://localhost:8000")
COOKIES = {
    # TODO Other login services like google etc
    "github": "github_access_token",
    "twitch": "twitch_access_token",
}

# TODO Add
# - Login with google
# - Login with facebook


@dataclass
class TwitchUser:
    id: int
    login: str
    display_name: str
    email: str


@dataclass
class GithubUser:
    id: int
    login: str


AVAILABLE_SERVICES_TYPE = Literal["twitch", "github", "facebook", "google"]
VALID_SERVICES: tuple[AVAILABLE_SERVICES_TYPE, ...] = typing.get_args(AVAILABLE_SERVICES_TYPE)


@dataclass
class LoggedInUser:
    id: int
    name: str
    service: AVAILABLE_SERVICES_TYPE

    @property
    def db_name(self) -> str:
        separator = " "  # TODO change if with facebook or google account, space in name is allowed
        return f"{self.name}{separator}{self.service}"

    def __post_init__(self):
        assert self.service in VALID_SERVICES, self.service


# MemoryStore https://docs.litestar.dev/2/usage/stores.html
twitch_cache = MemoryStore()
github_cache = MemoryStore()


async def provide_twitch_user(
    twitch_access_token: Annotated[str | None, Parameter(cookie=COOKIES["twitch"])] = None,
) -> TwitchUser | None:
    """
    Retrieves the user information from Twitch using the provided access token.
    """
    global twitch_cache
    if twitch_access_token is None:
        return None

    # Grab cached user information to reduce amount of requests to twitch api
    # pyre-fixme[9]
    cached_user: TwitchUser | None = await twitch_cache.get(twitch_access_token)
    if cached_user is not None:
        return cached_user

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

    # pyre-fixme[6]
    await twitch_cache.set(twitch_access_token, twitch_user, expires_in=60)
    return twitch_user


async def provide_github_user(
    github_access_token: Annotated[str | None, Parameter(cookie=COOKIES["github"])] = None,
) -> GithubUser | None:
    global github_cache
    if github_access_token is None:
        return None

    # Grab cached user information to reduce amount of requests to twitch api
    # pyre-fixme[9]
    cached_user: GithubUser | None = await github_cache.get(github_access_token)
    if cached_user is not None:
        return cached_user

    async with httpx.AsyncClient() as client:
        # https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/authorizing-oauth-apps
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

    # pyre-fixme[6]
    await github_cache.set(github_access_token, github_user, expires_in=60)
    return github_user


async def provide_logged_in_user(
    twitch_access_token: Annotated[str | None, Parameter(cookie=COOKIES["twitch"])] = None,
    github_access_token: Annotated[str | None, Parameter(cookie=COOKIES["github"])] = None,
) -> LoggedInUser | None:
    twitch_user = await provide_twitch_user(twitch_access_token)
    if twitch_user is not None:
        return LoggedInUser(id=twitch_user.id, name=twitch_user.display_name, service="twitch")
    github_user = await provide_github_user(github_access_token)
    if github_user is not None:
        return LoggedInUser(id=github_user.id, name=github_user.login, service="github")
    return None


async def owns_book_guard(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    logged_in_user: LoggedInUser | None = await provide_logged_in_user(
        connection.cookies.get(COOKIES["twitch"]),
        connection.cookies.get(COOKIES["github"]),
    )
    book_id: int = connection.path_params.get("book_id") or int(connection.query_params["book_id"])
    async with Prisma() as db:
        assert isinstance(book_id, int), book_id
        assert logged_in_user is not None
        assert isinstance(logged_in_user.name, str), logged_in_user.name
        book = await db.audiobookbook.find_first(
            where={
                "id": book_id,
                "uploaded_by": logged_in_user.db_name,
            }
        )
    if book is None:
        raise NotAuthorizedException("You don't have access to this book.")


async def is_logged_into_twitch_guard(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    """
    Can be used as a guard to make sure the user is logged into twitch
    https://docs.litestar.dev/2/usage/security/guards.html
    """
    twitch_user = await provide_twitch_user(connection.cookies.get(COOKIES["twitch"]))
    if twitch_user is None:
        raise NotAuthorizedException("You are not logged in to twitch.")


async def is_logged_in_guard(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    """
    Can be used as a guard to make sure the user is logged into twitch
    https://docs.litestar.dev/2/usage/security/guards.html
    """
    logged_in_user = await provide_logged_in_user(
        connection.cookies.get(COOKIES["twitch"]),
        connection.cookies.get(COOKIES["github"]),
    )
    if logged_in_user is None:
        raise NotAuthorizedException("You are not logged in to twitch, github, facebook or google.")


async def get_user_settings(
    voice_name: Annotated[str | None, Parameter(cookie="voice_name")] = None,
    voice_rate: Annotated[int | None, Parameter(cookie="voice_rate")] = None,
    voice_volume: Annotated[int | None, Parameter(cookie="voice_volume")] = None,
    voice_pitch: Annotated[int | None, Parameter(cookie="voice_pitch")] = None,
) -> AudioSettings:
    available_voices: list[str] = await get_supported_voices()
    return AudioSettings(
        voice_name=voice_name or available_voices[0],
        voice_rate=voice_rate or 0,
        voice_volume=voice_volume or 0,
        voice_pitch=voice_pitch or 0,
    )


# TODO get logged in username from cookies
