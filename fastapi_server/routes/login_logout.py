from __future__ import annotations

import os
from typing import Annotated

import aiohttp
from fastapi import APIRouter, Cookie
from fastapi.responses import RedirectResponse

login_router = APIRouter()

FRONTEND_SERVER_URL = os.getenv("FRONTEND_SERVER_URL", "0.0.0.0:8000")
CLIENT_ID = os.getenv("GITHUB_APP_CLIENT_ID", "1c200ded47490cce3b4d")
CLIENT_SECRET = os.getenv("GITHUB_APP_CLIENT_SECRET", "2aab3b1a609cb1a4126c7eec121bad2343332113")

# TODO Other login services like google, twitch etc


@login_router.get("/login")
async def user_login(code: str | None = None, ):
    # TODO Check/log where the request came from (ip or website?)
    if code is None:
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
        redirect = RedirectResponse(f"https://{FRONTEND_SERVER_URL}/chat")
        # TODO What does "secure" and "same_site" do?
        redirect.set_cookie(key="github_access_token", value=data["access_token"], secure=True)
        return redirect


@login_router.get("/logout")
async def user_logout(github_access_token: Annotated[str | None, Cookie()] = None):
    if github_access_token is None:
        # TODO Error, should not be able to log out if theres no cookie set
        return
    redirect = RedirectResponse(f"https://{FRONTEND_SERVER_URL}/chat")
    redirect.delete_cookie("github_access_token")
    return redirect
