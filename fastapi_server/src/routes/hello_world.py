import asyncio
import os
from typing import Literal

from litestar import Controller, MediaType, get
from loguru import logger

from prisma import Prisma

STAGE: Literal["local_dev", "dev", "prod", "test"] = os.getenv("STAGE")  # pyre-fixme[9]


class MyRootRoute(Controller):
    path = "/"

    @get("/test")
    async def index(self) -> str:
        return "Hello, world!"

    @get("/health-check")
    async def health_check(self) -> dict[str, str]:
        return {"hello": "world"}

    @get("/prisma-test", media_type=MediaType.TEXT)
    async def prisma_test(self) -> str:
        if STAGE == "test":
            async with Prisma() as db:
                await db.audiobookbook.create(
                    data={
                        "book_author": "test user",
                        "book_title": "test",
                        "uploaded_by": "test user",
                        "chapter_count": 100,
                    }
                )
                _results = await db.audiobookbook.find_many(where={})
        return "prisma success"


async def background_task_function(my_text: str, other_text: str = " something!"):
    """A background function that gets called once"""
    while 1:
        await asyncio.sleep(60 * 60)
        logger.info(f"Repeated {my_text}{other_text}")
