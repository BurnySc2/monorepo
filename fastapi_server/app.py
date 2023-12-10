import os
from typing import Literal

import uvicorn  # pyre-fixme[21]
from litestar import Litestar, get
from loguru import logger

from models.chat_messages import chat_create_tables
from models.todo_item import todo_create_tables
from routes.similar_words import MyWordsRoute

assert os.getenv("STAGE", "DEV") in {"DEV", "PROD"}, os.getenv("STAGE")
STAGE: Literal["DEV", "PROD"] = os.getenv("STAGE", "DEV")  # pyre-fixme[9]
BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "0.0.0.0:8000")


@get("/")
async def index() -> str:
    return "Hello, world!"


@get("/books/{book_id:int}")
async def get_book(book_id: int) -> dict[str, int]:
    return {"book_id": book_id}


async def startup_event():
    # asyncio.create_task(background_task_function('hello', other_text=' world!'))
    try:
        await todo_create_tables()
        await chat_create_tables()
    except ConnectionRefusedError:
        logger.error("Is postgres running?")
    logger.info("Started!")


def shutdown_event():
    logger.info("Bye world!")


app = Litestar(
    [index, get_book, MyWordsRoute],
    on_startup=[startup_event],
    on_shutdown=[shutdown_event],
)

if __name__ == "__main__":
    uvicorn.run(
        "__main__:app",
        host="0.0.0.0",
        port=8000,
        reload_delay=5,
        reload=BACKEND_SERVER_URL == "0.0.0.0:8000",
    )
