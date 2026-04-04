from __future__ import annotations

import os
import typing
from dataclasses import dataclass
from typing import Literal

import httpx
from dataclasses import dataclass
from dotenv import load_dotenv
from pydantic import BaseModel

_ = load_dotenv()

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "http://localhost:8000")

# Github app for local development
GITHUB_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "2aab3b1a609cb1a4126c7eec121bad2343332113")

# Twitch app for local development
TWITCH_CLIENT_ID = os.getenv("TWITCH_APP_CLIENT_ID", "ddgeuklh32bi15odtfc0o7gu4g4ehn")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_APP_CLIENT_SECRET", "mtu72a2v35p8x7f4fddwmzc2wwdruu")

# Facebook app for local development
FACEBOOK_CLIENT_ID = os.getenv("FACEBOOK_APP_CLIENT_ID", "1668878523656479")
FACEBOOK_CLIENT_SECRET = os.getenv("FACEBOOK_APP_CLIENT_SECRET", "dcd070e77fab0aabf1d468fe1d586e28")

# Google app for local development
GOOGLE_CLIENT_ID = os.getenv(
    "GOOGLE_APP_CLIENT_ID", "359432605842-cm653in48c8itjpk40j6vjcottc7541i.apps.googleusercontent.com"
)  # noqa: E501
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_APP_CLIENT_SECRET", "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")

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
        separator = " "  # TODO change if with facebook or google account, space in name is allowed
        return f"{self.name}{separator}{self.service}"

    def __post_init__(self):
        assert self.service in VALID_SERVICES, self.service


# class LoggedInUser(BaseModel):
#     id: int
#     name: str
#     service: AVAILABLE_SERVICES_TYPE

#     @classmethod
#     def from_service(cls, user: GithubUser | TwitchUser | GoogleUser | None) -> LoggedInUser | None:
#         if isinstance(user, TwitchUser):
#             return LoggedInUser(id=user.id, name=user.display_name, service="twitch")
#         if isinstance(user, GithubUser):
#             return LoggedInUser(id=user.id, name=user.login, service="github")
#         if isinstance(user, GoogleUser):
#             return LoggedInUser(id=user.id, name=user.display_name, service="google")
#         return None

#     @property
#     def db_name(self) -> str:
#         separator = " "  # TODO change if with facebook or google account, space in name is allowed
#         return f"{self.name}{separator}{self.service}"

#     def __post_init__(self):
#         assert self.service in VALID_SERVICES, self.service


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


async def provide_logged_in_user(loggin_settings: LoginSettings) -> LoggedInUser | None:
    user = None
    if loggin_settings.twitch_access_token is not None:
        user = await twitch_get_user(loggin_settings.twitch_access_token)
    if user is None and loggin_settings.github_access_token is not None:
        user = await github_get_user(loggin_settings.github_access_token)
    # TODO Add google
    return LoggedInUser.from_service(user)


# TODO: this was used by rio app, may be needed later for FastAPI sessions
# def logged_in_guard(event: rio.GuardEvent) -> str | None:
#     """
#     Check if the user is logged in at all
#     """
#     try:
#         _logged_in_user = event.session[LoggedInUser]
#     except KeyError:
#         return "/login"
