from __future__ import annotations

import typing
from dataclasses import dataclass
from typing import Annotated, Literal

import httpx
from fastapi import Cookie, HTTPException
from pydantic import BaseModel

from schemas.audiobook.db_models import AudiobookBook
from settings import settings

COOKIES = {
    "facebook": "facebook_access_token",
    "github": "github_access_token",
    "google": "google_access_token",
    "twitch": "twitch_access_token",
}


class TwitchUser(BaseModel):
    id: int
    login: str
    display_name: str
    email: str


class GithubUser(BaseModel):
    id: int
    login: str


class GoogleUser(BaseModel):
    id: int
    display_name: str


AVAILABLE_SERVICES_TYPE = Literal["twitch", "github", "google"]
VALID_SERVICES: tuple[AVAILABLE_SERVICES_TYPE, ...] = typing.get_args(AVAILABLE_SERVICES_TYPE)


@dataclass
class LoggedInUser:
    id: int
    name: str
    service: AVAILABLE_SERVICES_TYPE

    @classmethod
    def from_service(cls, user: GithubUser | TwitchUser | GoogleUser | None) -> LoggedInUser | None:
        if isinstance(user, TwitchUser):
            return LoggedInUser(id=user.id, name=user.display_name, service="twitch")
        if isinstance(user, GithubUser):
            return LoggedInUser(id=user.id, name=user.login, service="github")
        if isinstance(user, GoogleUser):
            return LoggedInUser(id=user.id, name=user.display_name, service="google")
        return None

    @property
    def db_name(self) -> str:
        # NOTE(auth-owner): separator assumes single-word names; revisit if facebook/google allow spaces.
        separator = " "
        return f"{self.name}{separator}{self.service}"

    def __post_init__(self):
        assert self.service in VALID_SERVICES, self.service


@dataclass
class LoginSettings:
    twitch_access_token: str | None = None
    github_access_token: str | None = None
    google_access_token: str | None = None
    user: LoggedInUser | None = None


async def twitch_get_user(twitch_access_token: str | None) -> TwitchUser | None:
    if twitch_access_token is None:
        return None
    async with httpx.AsyncClient() as client:
        # https://dev.twitch.tv/docs/api/reference/#get-users
        get_response = await client.get(
            url="https://api.twitch.tv/helix/users",
            headers={
                "Authorization": f"Bearer {twitch_access_token}",
                "Client-Id": settings.twitch_app_client_id or "",
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


async def google_get_user(google_access_token: str | None) -> GoogleUser | None:
    if google_access_token is None:
        return None
    async with httpx.AsyncClient() as client:
        get_response = await client.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={
                "Authorization": f"Bearer {google_access_token}",
            },
        )
        if get_response.is_error:
            return None
        data = get_response.json()
    google_user = GoogleUser(
        id=int(data["sub"]),
        display_name=data.get("name", "Unknown"),
    )
    return google_user


async def provide_logged_in_user(login_settings: LoginSettings) -> LoggedInUser | None:
    user = None
    if login_settings.twitch_access_token is not None:
        user = await twitch_get_user(login_settings.twitch_access_token)
    if user is None and login_settings.github_access_token is not None:
        user = await github_get_user(login_settings.github_access_token)
    if user is None and login_settings.google_access_token is not None:
        user = await google_get_user(login_settings.google_access_token)
    return LoggedInUser.from_service(user)


async def check_book_ownership(book: AudiobookBook, user: LoggedInUser) -> bool:
    return book.uploaded_by == user.db_name


async def get_current_user(
    twitch_access_token: Annotated[str | None, Cookie()] = None,
    github_access_token: Annotated[str | None, Cookie()] = None,
    google_access_token: Annotated[str | None, Cookie()] = None,
) -> LoggedInUser:
    login_settings = LoginSettings(
        twitch_access_token=twitch_access_token,
        github_access_token=github_access_token,
        google_access_token=google_access_token,
    )
    user = await provide_logged_in_user(login_settings)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user
