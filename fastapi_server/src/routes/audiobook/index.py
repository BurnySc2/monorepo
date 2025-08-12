from __future__ import annotations

from litestar import Controller, get
from litestar.di import Provide
from litestar.response import Template

from models.audiobook import AudiobookBook
from routes.cookies_and_guards import (
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
        books = (
            # pyrefly: ignore
            await AudiobookBook.objects()
            # pyrefly: ignore
            .where(AudiobookBook.uploaded_by == logged_in_user.db_name)
            .order_by(AudiobookBook.upload_date, ascending=False)
        )
        # return "You don't have any books uploaded."
        if len(books) == 0:
            return "You don't have any books uploaded."
        return Template(
            template_name="audiobook/overview_books.html",
            context={"books": books},
        )
