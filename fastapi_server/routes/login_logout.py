from __future__ import annotations

import os
from typing import Annotated

import aiohttp
from litestar import Controller, Response, get
from litestar.datastructures import Cookie
from litestar.params import Parameter
from litestar.response import Redirect
from litestar.status_codes import HTTP_302_FOUND, HTTP_409_CONFLICT, HTTP_503_SERVICE_UNAVAILABLE

# Github app for local development
CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")
CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "2aab3b1a609cb1a4126c7eec121bad2343332113")


# Github app for local development
CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")
CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "2aab3b1a609cb1a4126c7eec121bad2343332113")


COOKIES = {
    # TODO Other login services like google, twitch etc
    "github": "github_access_token",
}


class MyLoginRoute(Controller):
    path = "/login"

    @get("/github")
    async def user_login(
        self,
        code: str | None,
        github_access_token: Annotated[str | None, Parameter(cookie=COOKIES["github"])],
    ) -> Response | Redirect:
        # If 'code' is not set as a param, redirect to github page
        # which redirects to this page again with 'code' parameter
        if code is None:
            return Redirect(
                f"https://github.com/login/oauth/authorize?client_id={CLIENT_ID}",
                status_code=HTTP_302_FOUND,  # pyre-fixme[6]
            )

        # Access token has already been set before
        if github_access_token is not None:
            return Redirect(
                "/",
                status_code=HTTP_302_FOUND,  # pyre-fixme[6]
            )

        async with aiohttp.ClientSession() as session:
            url = "https://github.com/login/oauth/access_token"
            post_response = await session.post(
                url,
                headers={"Accept": "application/json"},
                json={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "code": code,
                },
            )
            if not post_response.ok:
                return Response("Github may be unavailable", status_code=HTTP_503_SERVICE_UNAVAILABLE)
            data = await post_response.json()
            if "error" in data:
                return Response("Error in json response. Try emptying your cookies", status_code=HTTP_409_CONFLICT)

            redirect = Redirect(
                "/",
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
        redirect = Redirect("/chat")
        for cookie_key in COOKIES.values():
            redirect.delete_cookie(cookie_key)
        return redirect
