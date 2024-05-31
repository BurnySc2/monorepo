from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

import httpx
from dotenv import load_dotenv
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.params import Parameter

from routes.audiobook.schema import (
    AudioSettings,
    book_table,
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


T = TypeVar("T", TwitchUser, GithubUser)


# TODO Replace with MemoryStore https://docs.litestar.dev/2/usage/stores.html
class UserCache(Generic[T]):
    def __init__(
        self,
        user_class: type[T],
        cache_duration_seconds: int,
    ):
        self.user_class = user_class
        self.cache_duration_seconds = cache_duration_seconds
        self.user_cache: dict[str, tuple[T, datetime.datetime]] = {}

    def __getitem__(self, access_token: str) -> T | None:
        cached_user, cache_expire_datetime = self.user_cache.get(access_token, (None, None))
        if cache_expire_datetime is not None and cache_expire_datetime > datetime.datetime.now(
            tz=datetime.timezone.utc
        ):
            return cached_user

    def __setitem__(self, access_token: str, user: T) -> T:
        assert isinstance(user, self.user_class)
        self.user_cache[access_token] = (
            user,
            datetime.datetime.now(tz=datetime.timezone.utc) + datetime.timedelta(seconds=self.cache_duration_seconds),
        )
        return user


twitch_cache = UserCache(user_class=TwitchUser, cache_duration_seconds=60)
github_cache = UserCache(user_class=GithubUser, cache_duration_seconds=60)


async def get_twitch_user(
    twitch_access_token: Annotated[str | None, Parameter(cookie=COOKIES["twitch"])] = None,
) -> TwitchUser | None:
    """
    Retrieves the user information from Twitch using the provided access token.
    """
    global twitch_cache
    if twitch_access_token is None:
        return None

    # Grab cached user information to reduce amount of requests to twitch api
    cached_user = twitch_cache[twitch_access_token]
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

    twitch_cache[twitch_access_token] = twitch_user
    return twitch_user


async def get_github_user(
    github_access_token: Annotated[str | None, Parameter(cookie=COOKIES["github"])] = None,
) -> GithubUser | None:
    global github_cache
    if github_access_token is None:
        return None

    # Grab cached user information to reduce amount of requests to twitch api
    cached_user = github_cache[github_access_token]
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

    github_cache[github_access_token] = github_user
    return github_user


async def owns_book_guard(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    twitch_user = await get_twitch_user(connection.cookies.get(COOKIES["twitch"]))
    book_id = connection.path_params.get("book_id") or connection.query_params["book_id"]
    # pyre-fixme[16]
    book_count = book_table.count(id=book_id, uploaded_by=twitch_user.display_name)
    if book_count == 0:
        raise NotAuthorizedException("You don't have access to this book.")


async def logged_into_twitch_guard(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    """
    Can be used as a guard to make sure the user is logged into twitch
    https://docs.litestar.dev/2/usage/security/guards.html
    """
    twitch_user = await get_twitch_user(connection.cookies.get(COOKIES["twitch"]))
    if twitch_user is None:
        raise NotAuthorizedException("You are not logged in to twitch.")


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
