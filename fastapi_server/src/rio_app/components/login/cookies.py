from __future__ import annotations

import os
import typing
from typing import Literal

import rio
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


class LoggedInUser(BaseModel):
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


class LoginSettings(rio.UserSettings):
    twitch_access_token: rio.HttpOnly[str | None] = None
    github_access_token: rio.HttpOnly[str | None] = None
    google_access_token: rio.HttpOnly[str | None] = None
