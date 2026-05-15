from __future__ import annotations

import os

import httpx
from fastapi import APIRouter, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse

from components.login.cookies import (
    BACKEND_SERVER_URL,
    COOKIES,
    GITHUB_CLIENT_ID,
    GOOGLE_CLIENT_ID,
    TWITCH_CLIENT_ID,
    LoginSettings,
    github_get_user,
    google_get_user,
    provide_logged_in_user,
    twitch_get_user,
)
from components.login.github import github_verify_code
from components.login.google import google_verify_code
from components.login.twitch import twitch_verify_code

login_router = APIRouter()


# Frontend URL for OAuth redirects
# Set via environment variable in production
def _get_frontend_url(request: Request) -> str:
    """Return the frontend base URL.

    * In production it is read from the ``FRONTEND_URL`` environment variable.
    * In development (``STAGE=dev``) we infer it from the incoming request
      ``Host`` header and scheme so the port can change dynamically.
    """
    # Production override – use explicit env var if set
    env_url = os.getenv("FRONTEND_URL")
    if env_url:
        return env_url.rstrip("/")
    # Development – construct from request (any localhost port)
    scheme = request.url.scheme
    host = request.headers.get("host", "localhost")
    return f"{scheme}://{host}"


@login_router.get("/login")
async def get_login_status(request: Request) -> JSONResponse:
    """
    Check if user is logged in by reading cookies.
    Returns user info if logged in, None otherwise.
    """
    login_settings = LoginSettings(
        twitch_access_token=request.cookies.get(COOKIES["twitch"]),
        github_access_token=request.cookies.get(COOKIES["github"]),
        google_access_token=request.cookies.get(COOKIES["google"]),
    )
    logged_in_user = await provide_logged_in_user(login_settings)
    if logged_in_user is None:
        return JSONResponse({"logged_in": False})
    return JSONResponse(
        {
            "logged_in": True,
            "user": {
                "id": logged_in_user.id,
                "name": logged_in_user.name,
                "service": logged_in_user.service,
            },
        }
    )


@login_router.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """
    Clear all authentication cookies and redirect to login page.
    """
    response = RedirectResponse(url=_get_frontend_url(request))
    # Delete all auth cookies
    for cookie_name in COOKIES.values():
        response.delete_cookie(cookie_name)
    return response


@login_router.get("/login/twitch")
async def twitch_login_callback(
    request: Request,
    code: str | None = Query(default=None),
) -> RedirectResponse:
    """
    Handle Twitch OAuth callback.
    If code provided, exchange for token and set cookie.
    If already logged in, redirect to login page.
    """
    twitch_access_token = request.cookies.get(COOKIES["twitch"])

    # Check if already logged in with twitch
    if twitch_access_token is not None:
        user = await twitch_get_user(twitch_access_token)
        if user is not None:
            return RedirectResponse(url=_get_frontend_url(request))

    # No code provided, redirect to login
    if code is None:
        return RedirectResponse(url=_get_frontend_url(request))

    # Exchange code for access token
    access_token = await twitch_verify_code(code)

    if isinstance(access_token, int):
        # Error occurred
        return RedirectResponse(url=(_get_frontend_url(request) + "/login?error=oauth_failed"))

    # Set cookie and redirect
    response = RedirectResponse(url=_get_frontend_url(request))
    response.set_cookie(
        key=COOKIES["twitch"],
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        # 7 days
        max_age=604800,
    )
    return response


@login_router.get("/login/github")
async def github_login_callback(
    request: Request,
    code: str | None = Query(default=None),
) -> RedirectResponse:
    """
    Handle GitHub OAuth callback.
    If code provided, exchange for token and set cookie.
    If already logged in, redirect to login page.
    """
    github_access_token = request.cookies.get(COOKIES["github"])

    # Check if already logged in with github
    if github_access_token is not None:
        user = await github_get_user(github_access_token)
        if user is not None:
            return RedirectResponse(url=_get_frontend_url(request))

    # No code provided, redirect to login
    if code is None:
        return RedirectResponse(url=_get_frontend_url(request))

    # Exchange code for access token
    access_token = await github_verify_code(code)

    if isinstance(access_token, int):
        # Error occurred
        return RedirectResponse(url=(_get_frontend_url(request) + "/login?error=oauth_failed"))

    # Set cookie and redirect
    response = RedirectResponse(url=_get_frontend_url(request))
    response.set_cookie(
        key=COOKIES["github"],
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        # 7 days
        max_age=604800,
    )
    return response


@login_router.get("/login/google")
async def google_login_callback(
    request: Request,
    code: str | None = Query(default=None),
) -> RedirectResponse:
    """
    Handle Google OAuth callback.
    If code provided, exchange for token and set cookie.
    If already logged in, redirect to login page.
    """
    google_access_token = request.cookies.get(COOKIES["google"])

    # Check if already logged in with google
    if google_access_token is not None:
        user = await google_get_user(google_access_token)
        if user is not None:
            return RedirectResponse(url=_get_frontend_url(request))

    # No code provided, redirect to login
    if code is None:
        return RedirectResponse(url=_get_frontend_url(request))

    # Exchange code for access token
    access_token = await google_verify_code(code)

    if isinstance(access_token, int):
        # Error occurred
        return RedirectResponse(url=(_get_frontend_url(request) + "/login?error=oauth_failed"))

    # Set cookie and redirect
    response = RedirectResponse(url=_get_frontend_url(request))
    response.set_cookie(
        key=COOKIES["google"],
        value=access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        # 7 days
        max_age=604800,
    )
    return response


@login_router.get("/login/twitch/start")
async def start_twitch_login() -> RedirectResponse:
    """
    Start Twitch OAuth flow - redirects to Twitch authorization page.
    """

    oauth_url = httpx.URL(
        "https://id.twitch.tv/oauth2/authorize",
        params={
            "client_id": TWITCH_CLIENT_ID,
            "redirect_uri": f"{BACKEND_SERVER_URL}/login/twitch",
            "response_type": "code",
            "scope": "user:read:email",
        },
    )
    return RedirectResponse(url=str(oauth_url))


@login_router.get("/login/github/start")
async def start_github_login() -> RedirectResponse:
    """
    Start GitHub OAuth flow - redirects to GitHub authorization page.
    """

    oauth_url = httpx.URL(
        "https://github.com/login/oauth/authorize",
        params={
            "client_id": GITHUB_CLIENT_ID,
            "redirect_uri": f"{BACKEND_SERVER_URL}/login/github",
            "response_type": "code",
            "scope": "read:user",
        },
    )
    return RedirectResponse(url=str(oauth_url))


@login_router.get("/login/google/start")
async def start_google_login() -> RedirectResponse:
    """
    Start Google OAuth flow - redirects to Google authorization page.
    """

    oauth_url = httpx.URL(
        "https://accounts.google.com/o/oauth2/v2/auth",
        params={
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": f"{BACKEND_SERVER_URL}/login/google",
            "response_type": "code",
            "scope": "profile",
        },
    )
    return RedirectResponse(url=str(oauth_url))
