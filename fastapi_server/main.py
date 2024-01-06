import os
from typing import Literal

import uvicorn  # pyre-fixme[21]
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from models.chat_messages import chat_create_tables
from models.todo_item import todo_create_tables
from routes.htmx_chat import htmx_chat_router
from routes.htmx_todolist import htmx_todolist_router
from routes.login_logout import login_router

assert os.getenv("STAGE", "DEV") in {"DEV", "PROD"}, os.getenv("STAGE")
STAGE: Literal["DEV", "PROD"] = os.getenv("STAGE", "DEV")  # pyre-fixme[9]
BACKEND_SERVER_URL = os.getenv("BACKEND_SERVER_URL", "0.0.0.0:8000")

app = FastAPI()
app.include_router(htmx_todolist_router)
app.include_router(htmx_chat_router)
app.include_router(login_router)

origins = [
    "https://burnysc2.github.io",
    "https://replaycomparer.netlify.app",
    "https://burnysc2-monorepo.netlify.app",
    "https://burnysc2-monorepo-dev.netlify.app",
]

logger.info(f"Starting in 'STAGE == {STAGE}' mode")
if BACKEND_SERVER_URL == "0.0.0.0:8000":
    origins += [f"http://localhost:{i}" for i in range(1, 2**16)]
    origins += [f"https://localhost:{i}" for i in range(1, 2**16)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    # asyncio.create_task(background_task_function('hello', other_text=' world!'))
    try:
        await todo_create_tables()
        await chat_create_tables()
    except ConnectionRefusedError:
        logger.error("Is postgres running?")
    logger.info("Started!")


@app.on_event("shutdown")
def shutdown_event():
    logger.info("Bye world!")


if __name__ == "__main__":
    uvicorn.run(
        "__main__:app",
        host="0.0.0.0",
        port=8000,
        reload=BACKEND_SERVER_URL == "0.0.0.0:8000",
        # Enable ssl when developing locally
        ssl_keyfile="helper/app-key.pem" if BACKEND_SERVER_URL == "0.0.0.0:8000" else None,
        ssl_certfile="helper/app.pem" if BACKEND_SERVER_URL == "0.0.0.0:8000" else None,
    )
