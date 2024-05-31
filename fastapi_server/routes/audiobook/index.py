from __future__ import annotations

from litestar import Controller, get
from litestar.di import Provide
from litestar.response import Template

from routes.login_logout import TwitchUser, get_twitch_user


class MyAudiobookIndexRoute(Controller):
    path = "/audiobook"
    # TODO Guard: Logged in to some service
    dependencies = {
        "twitch_user": Provide(get_twitch_user),
    }

    @get("/")
    async def index(
        self,
        twitch_user: TwitchUser | None,
    ) -> Template:
        return Template(template_name="audiobook/index.html")

    @get("/list_books")
    async def list_books(
        self,
        twitch_user: TwitchUser | None,
    ) -> str:
        # TODO The endpoint "/" should list all uploaded books by user, then be able to navigate to it
        # TODO List all uploaded books
        # If not logged in: show "NOT LOGGED IN"
        return "TODO my list of books"
