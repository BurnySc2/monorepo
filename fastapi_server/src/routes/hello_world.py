import asyncio
import os
from typing import Literal

from litestar import Controller, MediaType, get
from litestar.response import Template
from loguru import logger

from models.audiobook import AudiobookBook

# pyrefly: ignore
STAGE: Literal["local_dev", "dev", "prod", "test"] = os.getenv("STAGE")


class MyRootRoute(Controller):
    path = "/"

    @get("/")
    async def index(self) -> Template:
        return Template(template_name="index.html")

    @get("/test")
    async def test(self) -> str:
        return "Hello, world!"

    @get("/health-check")
    async def health_check(self) -> dict[str, str]:
        return {"hello": "world"}

    @get("/piccolo-test", media_type=MediaType.TEXT)
    async def prisma_test(self) -> str:
        if STAGE == "test":
            await AudiobookBook(
                book_author="test user",
                book_title="test",
                uploaded_by="test user",
                chapter_count=100,
            ).save()
            _results = await AudiobookBook.objects()
        return "piccolo success"


async def background_task_function(my_text: str, other_text: str = " something!"):
    """A background function that gets called once"""
    while True:
        await asyncio.sleep(60 * 60)
        logger.info(f"Repeated {my_text}{other_text}")
