import asyncio

from fastapi.routing import APIRouter
from loguru import logger

hello_world_router = APIRouter()


@hello_world_router.get('/')
def hello_world():
    return {'Hello': 'World'}


async def background_task_function(my_text: str, other_text: str = ' something!'):
    """A background function that gets called once"""
    while 1:
        await asyncio.sleep(60 * 60)
        logger.info(f'Repeated {my_text}{other_text}')
