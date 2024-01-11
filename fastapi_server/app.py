import asyncio
import os
from pathlib import Path
from typing import Literal

import uvicorn  # pyre-fixme[21]
from dotenv import load_dotenv
from litestar import Litestar, MediaType, get
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.template.config import TemplateConfig
from loguru import logger

from models.chat_messages import chat_create_tables
from models.todo_item import todo_create_tables
from routes.hello_world import MyRootRoute

# from routes.similar_words import MyWordsRoute
from routes.text_to_speech import MyTTSRoute
from routes.tts.websocket_handler import TTSQueue, TTSWebsocketHandler

load_dotenv()


# Paths and folders of permanent data
DATA_FOLDER = Path(__file__).parent / "data"
logger.add(DATA_FOLDER / "app.log")

assert os.getenv("STAGE", "DEV") in {"DEV", "PROD"}, os.getenv("STAGE")
STAGE: Literal["DEV", "PROD"] = os.getenv("STAGE", "DEV")  # pyre-fixme[9]
BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "0.0.0.0:8000")
WS_BACKEND_SERVER_URL = os.getenv("BACKEND_WS_SERVER_URL", "ws:0.0.0.0:8000")


@get(path="/", media_type=MediaType.TEXT)
async def index() -> str:
    return "Hello, world!"


@get("/books/{book_id:int}")
async def get_book(book_id: int) -> dict[str, int]:
    return {"book_id": book_id}


async def startup_event():
    # Run websocket handler which handles tts
    asyncio.create_task(TTSQueue.start_irc_bot())

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
    [index, get_book, MyRootRoute, MyTTSRoute, TTSWebsocketHandler],
    on_startup=[startup_event],
    on_shutdown=[shutdown_event],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
)

if __name__ == "__main__":
    uvicorn.run(
        "__main__:app",
        host="0.0.0.0",
        port=8000,
        reload_delay=5,
        reload=BACKEND_SERVER_URL == "0.0.0.0:8000",
        debug=True,
    )
