from __future__ import annotations

import os
from typing import Annotated

import aiohttp
from fastapi import APIRouter, Cookie, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

login_router = APIRouter()
login_templates = Jinja2Templates(directory="frontend/login")
logout_templates = Jinja2Templates(directory="frontend/logout")

FRONTEND_SERVER_URL = os.getenv("FRONTEND_SERVER_URL", "0.0.0.0:8000")
# Github app for local development
CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")
CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "2aab3b1a609cb1a4126c7eec121bad2343332113")

BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "0.0.0.0:8000")

# TODO Other login services like google, twitch etc


# TODO Disable in production as it should be served by frontend, not by backend
@login_router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return login_templates.TemplateResponse("index.html", {"request": request, "server_url": BACKEND_SERVER_URL})


# TODO Disable in production as it should be served by frontend, not by backend
@login_router.get("/logout", response_class=HTMLResponse)
def logout_page(request: Request):
    return logout_templates.TemplateResponse("index.html", {"request": request, "server_url": BACKEND_SERVER_URL})


@login_router.get("/htmxapi/login")
async def user_login(
    response: Response,
    code: Annotated[str | None, Cookie()] = None,
    github_access_token: Annotated[str | None, Cookie()] = None
):
    # TODO Check/log where the request came from (ip or website?)
    if code is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return
    if github_access_token is not None:
        response.delete_cookie(key="code")
        response.status_code = status.HTTP_204_NO_CONTENT
        return

    url = "https://github.com/login/oauth/access_token"
    async with aiohttp.ClientSession() as session:
        post_response = await session.post(
            url,
            headers={"Accept": "application/json"},
            json={
                "client_id": CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "code": code,
            }
        )
        if not post_response.ok:
            return "error etc"
        data = await post_response.json()
        if "error" in data:
            return "wrong client id code"
        redirect = RedirectResponse("/htmxapi/chatheader")
        # TODO What does "secure" and "same_site" do?
        redirect.set_cookie(key="github_access_token", value=data["access_token"], secure=True)
        redirect.delete_cookie(key="code")
        return redirect
