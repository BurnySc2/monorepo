import asyncio
import os
from pathlib import Path
from typing import Literal

import uvicorn
from dotenv import load_dotenv
from litestar import Litestar
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.static_files import create_static_files_router
from litestar.template.config import TemplateConfig
from loguru import logger

from routes.audiobook.book import MyAudiobookBookRoute
from routes.audiobook.epub_upload import MyAudiobookEpubRoute
from routes.audiobook.index import MyAudiobookIndexRoute
from routes.hello_world import MyRootRoute

# from routes.htmx_chat import MyChatRoute
# from routes.htmx_todolist import MyTodoRoute
from routes.login_logout import MyLoginRoute, MyLogoutRoute

# from routes.similar_words import MyWordsRoute
from routes.text_to_speech import MyTTSRoute
from routes.tts.websocket_handler import TTSQueue, TTSWebsocketHandler
from workers.prevent_overflowing_audiobook_bucket import prevent_overflowing_audiobook_bucket

load_dotenv()


# Paths and folders of permanent data
DATA_FOLDER = Path(__file__).parent / "data"
DATA_FOLDER.mkdir(parents=True, exist_ok=True)
logger.add(DATA_FOLDER / "app.log")

assert os.getenv("STAGE", "dev") in {"local_dev", "dev", "prod", "test"}, os.getenv("STAGE")
STAGE: Literal["local_dev", "dev", "prod", "test"] = os.getenv("STAGE")  # pyre-fixme[9]
BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "http://0.0.0.0:8000")
WS_BACKEND_SERVER_URL = os.getenv("BACKEND_WS_SERVER_URL", "ws:http://0.0.0.0:8000")


async def startup_event():
    # Run websocket handler which handles tts
    asyncio.create_task(TTSQueue.start_irc_bot())
    # Remove books and minio objects if minio bucket is overflowing
    asyncio.create_task(prevent_overflowing_audiobook_bucket())
    logger.info("Started!")


def shutdown_event():
    logger.info("Bye world!")


app = Litestar(
    route_handlers=[
        MyAudiobookBookRoute,
        MyAudiobookIndexRoute,
        MyAudiobookEpubRoute,
        # MyChatRoute,
        MyLoginRoute,
        MyLogoutRoute,
        MyRootRoute,
        # MyTodoRoute,
        MyTTSRoute,
        TTSWebsocketHandler,
        create_static_files_router(path="/static", directories=["assets"]),
    ],
    on_startup=[startup_event],
    on_shutdown=[shutdown_event],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
    debug=BACKEND_SERVER_URL == "http://0.0.0.0:8000",
)

if __name__ == "__main__":
    uvicorn.run(
        "__main__:app",
        host="0.0.0.0",
        port=8000,
        reload_delay=5,
        reload=BACKEND_SERVER_URL == "http://0.0.0.0:8000",
    )
