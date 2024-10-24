from __future__ import annotations

import os

from dotenv import load_dotenv
from litestar.connection import ASGIConnection
from litestar.exceptions import NotAuthorizedException
from litestar.handlers.base import BaseRouteHandler

from src.routes.cookies_and_guards import COOKIES, provide_logged_in_user

load_dotenv()

# pyre-fixme[16]
ALLOWED_LIST_OF_TWITCH_USERS = set(os.getenv("ALLOWED_TWITCH_USERS_FOR_TELEGRAM_BROWSER").lower().split(";"))


async def is_logged_in_allowed_accounts_guard(
    connection: ASGIConnection,
    _: BaseRouteHandler,
) -> None:
    """
    Can be used as a guard to make sure the user is logged into twitch and one of the allowed names
    https://docs.litestar.dev/2/usage/security/guards.html
    """
    twitch_user = await provide_logged_in_user(twitch_access_token=connection.cookies.get(COOKIES["twitch"]))
    if twitch_user is None:
        raise NotAuthorizedException("You are not logged in to twitch.")
    if twitch_user.db_name.lower() not in ALLOWED_LIST_OF_TWITCH_USERS:
        raise NotAuthorizedException("You are not allowed to view this page.")
