from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse, RedirectResponse
from loguru import logger

from components.login.cookies import (
    COOKIES,
    LoginSettings,
    provide_logged_in_user,
)
from components.login.providers import PROVIDERS, OAuthProvider
from settings import settings

login_router = APIRouter()
LOGIN_MAX_AGE = 84_400  # 7 days in seconds


# Frontend URL for OAuth redirects
# Set via environment variable in production
def _get_frontend_url() -> str:
    """Return the frontend base URL from settings (``FRONTEND_URL`` environment variable)."""
    return settings.frontend_url.rstrip("/")


async def _handle_oauth_callback(
    provider: OAuthProvider,
    request: Request,
    code: str | None,
) -> RedirectResponse:
    """Shared OAuth callback logic for all providers."""
    access_token = request.cookies.get(provider.cookie_key)

    # Check if already logged in with this provider
    if access_token is not None:
        user = await provider.get_user(access_token)
        if user is not None:
            return RedirectResponse(url=_get_frontend_url())

    # No code provided, redirect to login
    if code is None:
        return RedirectResponse(url=_get_frontend_url())

    # Exchange code for access token
    token_or_error = await provider.verify_code(code)

    if isinstance(token_or_error, int):
        # Error occurred
        return RedirectResponse(url=(_get_frontend_url() + "/?error=oauth_failed"))

    # Set cookie and redirect
    response = RedirectResponse(url=_get_frontend_url())
    # Secure cookies only outside dev/test (dev uses http://localhost, Secure would drop cookie).
    is_secure = settings.stage not in ("dev", "test", "")
    response.set_cookie(
        key=provider.cookie_key,
        value=token_or_error,
        httponly=True,
        secure=is_secure,
        samesite="lax",
        max_age=LOGIN_MAX_AGE,
    )
    return response


def _start_oauth(provider: OAuthProvider) -> RedirectResponse:
    """Shared OAuth start logic for all providers."""
    # Fail-closed when OAuth client_id is missing (do not emit client_id=None).
    if not provider.client_id:
        logger.error(f"OAuth not configured for provider {provider.name!r}: missing client_id")
        raise HTTPException(status_code=500, detail=f"OAuth not configured for {provider.name}")
    oauth_url = httpx.URL(
        provider.authorize_url,
        params={
            "client_id": provider.client_id,
            "redirect_uri": f"{settings.backend_server_url}{provider.redirect_path}",
            "response_type": "code",
            "scope": provider.scope,
        },
    )
    return RedirectResponse(url=str(oauth_url))


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
    response = RedirectResponse(url=_get_frontend_url())
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
    return await _handle_oauth_callback(PROVIDERS["twitch"], request, code)


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
    return await _handle_oauth_callback(PROVIDERS["github"], request, code)


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
    return await _handle_oauth_callback(PROVIDERS["google"], request, code)


@login_router.get("/login/twitch/start")
async def start_twitch_login() -> RedirectResponse:
    """
    Start Twitch OAuth flow - redirects to Twitch authorization page.
    """
    return _start_oauth(PROVIDERS["twitch"])


@login_router.get("/login/github/start")
async def start_github_login() -> RedirectResponse:
    """
    Start GitHub OAuth flow - redirects to GitHub authorization page.
    """
    return _start_oauth(PROVIDERS["github"])


@login_router.get("/login/google/start")
async def start_google_login() -> RedirectResponse:
    """
    Start Google OAuth flow - redirects to Google authorization page.
    """
    return _start_oauth(PROVIDERS["google"])
