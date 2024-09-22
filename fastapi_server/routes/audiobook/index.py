from __future__ import annotations

from litestar import Controller, get
from litestar.di import Provide
from litestar.response import Template

from routes.cookies_and_guards import (
    LoggedInUser,
    is_logged_in_guard,
    provide_logged_in_user,
)


class MyAudiobookIndexRoute(Controller):
    path = "/audiobook"
    # TODO Guard: Logged in to some service
    dependencies = {
        "logged_in_user": Provide(provide_logged_in_user),
    }

    @get("/")
    async def index(
        self,
    ) -> Template:
        return Template(template_name="audiobook/index.html")

    @get("/list_books", guards=[is_logged_in_guard])
    async def list_books(
        self,
        logged_in_user: LoggedInUser,
        # TODO Add "logged in" guard
    ) -> str:
        # TODO The endpoint "/" should list all uploaded books by user, then be able to navigate to it
        # TODO List all uploaded books
        # If not logged in: show "NOT LOGGED IN"
        return "TODO my list of books"
