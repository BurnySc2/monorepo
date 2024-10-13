import asyncio

from litestar import Controller, get
from loguru import logger


class MyRootRoute(Controller):
    path = "/"

    @get("/test")
    async def index(self) -> str:
        return "Hello, world!"

    @get("/health-check")
    async def health_check(self) -> dict[str, str]:
        return {"hello": "world"}


async def background_task_function(my_text: str, other_text: str = " something!"):
    """A background function that gets called once"""
    while 1:
        await asyncio.sleep(60 * 60)
        logger.info(f"Repeated {my_text}{other_text}")
