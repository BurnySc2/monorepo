from __future__ import annotations

import datetime
import os
from dataclasses import dataclass
from typing import Annotated, Generic, TypeVar

import httpx
from dotenv import load_dotenv
from litestar import Controller, Response, get
from litestar.connection import ASGIConnection
from litestar.datastructures import Cookie
from litestar.di import Provide
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler
from litestar.params import Parameter
from litestar.response import Redirect, Template
from litestar.status_codes import HTTP_302_FOUND, HTTP_409_CONFLICT, HTTP_503_SERVICE_UNAVAILABLE

load_dotenv()


# Github app for local development
GITHUB_CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "2aab3b1a609cb1a4126c7eec121bad2343332113")

TWITCH_CLIENT_ID = os.getenv("TWITCH_APP_CLIENT_ID", "ddgeuklh32bi15odtfc0o7gu4g4ehn")
TWITCH_CLIENT_SECRET = os.getenv("TWITCH_APP_CLIENT_SECRET", "mtu72a2v35p8x7f4fddwmzc2wwdruu")

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "http://localhost:8000")

COOKIES = {
    # TODO Other login services like google etc
    "github": "github_access_token",
    "twitch": "twitch_access_token",
}


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


class MyLoginRoute(Controller):
    path = "/login"
    # https://docs.litestar.dev/2/usage/dependency-injection.html
    dependencies = {
        "twitch_user": Provide(get_twitch_user),
        "github_user": Provide(get_github_user),
    }

    @get("/")
    async def login(
        self,
        twitch_user: TwitchUser | None,
        github_user: GithubUser | None,
    ) -> Template:
        return Template(
            template_name="login/index.html",
            context={
                "twitch_user": twitch_user,
                "github_user": github_user,
            },
        )

    @get("/twitchtest", guards=[logged_into_twitch_guard])
    async def requires_twitch_logged_in(
        self,
    ) -> str:
        return "This route is only available for logged in users"

    @get("/twitch")
    async def twitch_login(
        self,
        twitch_user: TwitchUser | None,
        code: str | None,
    ) -> Response | Redirect:
        if twitch_user is not None:
            # User is already logged in
            return Redirect(
                "/login",
                # Does this have an effect?
                status_code=HTTP_302_FOUND,  # pyre-fixme[6]
            )
        if code is None:
            return Redirect(
                # TODO encode URI
                f"https://id.twitch.tv/oauth2/authorize?client_id={TWITCH_CLIENT_ID}&redirect_uri={BACKEND_SERVER_URL}/login/twitch&response_type=code&scope=user:read:email",
                # pyre-fixme[6]
                status_code=HTTP_302_FOUND,
            )

        # Code was given, get access token and set cookie
        async with httpx.AsyncClient() as client:
            url = "https://id.twitch.tv/oauth2/token"
            post_response = await client.post(
                url,
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
                return Response("Twitch may be unavailable", status_code=HTTP_503_SERVICE_UNAVAILABLE)
            data = post_response.json()
        if "error" in data:
            return Response("Error in json response. Try clearing your cookies", status_code=HTTP_409_CONFLICT)
        redirect = Redirect(
            "/login",
            status_code=HTTP_302_FOUND,  # pyre-fixme[6]
        )
        redirect.set_cookie(
            Cookie(
                key=COOKIES["twitch"],
                value=data["access_token"],
                # Is this required?
                # secure=True,
            )
        )
        return redirect

    @get("/github")
    async def github_login(
        self,
        github_user: GithubUser | None,
        code: str | None,
    ) -> Response | Redirect:
        """
        This is the /login/github endpoint to log the user into a github account.
        """
        if github_user is not None:
            # User is already logged in
            return Redirect(
                "/login",
                status_code=HTTP_302_FOUND,  # pyre-fixme[6]
            )
        # If 'code' is not set as a param, redirect to github page
        # which redirects to this page again with 'code' parameter
        if code is None:
            return Redirect(
                f"https://github.com/login/oauth/authorize?client_id={GITHUB_CLIENT_ID}&scope=read:user",
                status_code=HTTP_302_FOUND,  # pyre-fixme[6]
            )

        # Code was given, get access token and set cookie
        async with httpx.AsyncClient() as client:
            url = "https://github.com/login/oauth/access_token"
            post_response = await client.post(
                url,
                headers={"Accept": "application/json"},
                json={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code,
                },
            )
            if post_response.is_error:
                return Response("Github may be unavailable", status_code=HTTP_503_SERVICE_UNAVAILABLE)
            data = post_response.json()
        if "error" in data:
            return Response("Error in json response. Try clearing your cookies", status_code=HTTP_409_CONFLICT)

        redirect = Redirect(
            "/login",
            status_code=HTTP_302_FOUND,  # pyre-fixme[6]
        )
        redirect.set_cookie(
            Cookie(
                key=COOKIES["github"],
                value=data["access_token"],
                # Is this required?
                # secure=True,
            )
        )
        return redirect


class MyLogoutRoute(Controller):
    path = "/logout"

    @get("/", status_code=HTTP_302_FOUND)
    async def user_logout(self) -> Redirect:
        redirect = Redirect("/login")
        for cookie_key in COOKIES.values():
            redirect.delete_cookie(cookie_key)
        return redirect
