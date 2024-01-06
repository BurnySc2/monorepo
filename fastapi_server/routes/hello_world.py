import asyncio

from litestar import Controller, get
from loguru import logger


class MyRootRoute(Controller):
    path = "/"

    @get("/test")
    async def index(self) -> dict[str, str]:
        return {"Hello": "World"}


async def background_task_function(my_text: str, other_text: str = " something!"):
    """A background function that gets called once"""
    while 1:
        await asyncio.sleep(60 * 60)
        logger.info(f"Repeated {my_text}{other_text}")
