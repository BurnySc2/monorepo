from __future__ import annotations

import httpx
from litestar import Controller, Response, get
from litestar.datastructures import Cookie
from litestar.di import Provide
from litestar.response import Redirect, Template
from litestar.status_codes import (
    HTTP_302_FOUND,
    HTTP_409_CONFLICT,
    HTTP_503_SERVICE_UNAVAILABLE,
)

from routes.cookies_and_guards import (
    BACKEND_SERVER_URL,
    COOKIES,
    GITHUB_CLIENT_ID,
    GITHUB_CLIENT_SECRET,
    TWITCH_CLIENT_ID,
    TWITCH_CLIENT_SECRET,
    GithubUser,
    TwitchUser,
    is_logged_into_twitch_guard,
    provide_github_user,
    provide_twitch_user,
)


class MyLoginRoute(Controller):
    path = "/login"
    # https://docs.litestar.dev/2/usage/dependency-injection.html
    dependencies = {
        "twitch_user": Provide(provide_twitch_user),
        "github_user": Provide(provide_github_user),
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

    @get("/name")
    async def nav_name(
        self,
        twitch_user: TwitchUser | None,
        github_user: GithubUser | None,
    ) -> str:
        """Provides the current user name if logged in for the nav bar."""
        if twitch_user is not None:
            return twitch_user.display_name
        if github_user is not None:
            return github_user.login
        return "Login"

    # @get("/name_with_badge")
    # async def nav_name_with_badge(
    #     self,
    #     twitch_user: TwitchUser | None,
    #     github_user: GithubUser | None,
    # ) -> str:
    #     """Provides the current user name with icon if logged in for the nav bar."""
    #     # TODO show facebook/google/twitch/github icon next to name?
    #     if twitch_user is not None:
    #         return twitch_user.display_name
    #     if github_user is not None:
    #         return github_user.login
    #     return "Login"

    @get("/twitchtest", guards=[is_logged_into_twitch_guard])
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
            # pyre-fixme[6]
            return Redirect("/login", status_code=HTTP_302_FOUND)
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
        # pyre-fixme[6]
        redirect = Redirect("/login", status_code=HTTP_302_FOUND)
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
            # pyre-fixme[6]
            return Redirect("/login", status_code=HTTP_302_FOUND)
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
        # pyre-fixme[6]
        redirect = Redirect("/login", status_code=HTTP_302_FOUND)
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

    @get("/")
    async def user_logout(self) -> Redirect:
        # pyre-fixme[6]
        redirect = Redirect("/login", status_code=HTTP_302_FOUND)
        for cookie_key in COOKIES.values():
            redirect.delete_cookie(cookie_key)
        return redirect
