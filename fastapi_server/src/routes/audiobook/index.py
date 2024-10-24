from __future__ import annotations

from litestar import Controller, get
from litestar.di import Provide
from litestar.response import Template

from src.routes.caches import get_db
from src.routes.cookies_and_guards import (
    LoggedInUser,
    is_logged_in_guard,
    provide_logged_in_user,
)


class MyAudiobookIndexRoute(Controller):
    path = "/audiobook"
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
    ) -> Template | str:
        # Book Title, Book Author, chapters, Uploaded Date, delete button
        async with get_db() as db:
            books = await db.audiobookbook.find_many(
                where={
                    "uploaded_by": logged_in_user.db_name,
                },
                order=[{"upload_date": "desc"}],
            )
        if len(books) == 0:
            return "You don't have any books uploaded."
        return Template(
            template_name="audiobook/overview_books.html",
            context={"books": books},
        )
