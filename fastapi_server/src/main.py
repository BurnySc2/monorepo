"""Entry point for the FastAPI server.

Provides a minimal FastAPI application that can be started via the
VS Code launch configuration added above.
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routes.audiobook import audiobook_router
from routes.index import IndexRouter
from routes.login import login_router
from routes.raceroom import raceroom_router
from routes.replay_comparer import replay_comparer_router
from routes.replay_parser import replay_parser_router
from routes.tts_generate import tts_generate_router
from routes.tts_websocket import TTSRouter
from s3_helper import initialize_rustfs

RUSTFS_AUDIOBOOK_BUCKET = os.getenv("RUSTFS_AUDIOBOOK_BUCKET", "rustfs-audiobook-bucket")
RUSTFS_AUDIOBOOK_MAX_SIZE_MB = int(os.getenv("RUSTFS_AUDIOBOOK_MAX_SIZE_MB", "100000"))
RUSTFS_KEY_NAME = os.getenv("RUSTFS_KEY_NAME", "audiobook-key")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_rustfs()
    yield
    # End


app = FastAPI(lifespan=lifespan)

# Enable CORS only in development mode
if os.getenv("STAGE") == "dev":
    # Allow the Svelte dev server to talk to the API
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
# TODO Allow prod server frontend?


# Include the routers with appropriate prefixes
app.include_router(IndexRouter, prefix="/api")
app.include_router(login_router)
app.include_router(replay_parser_router, prefix="/api")
app.include_router(TTSRouter, prefix="/tts-api")
app.include_router(tts_generate_router, prefix="/tts-generate")
app.include_router(audiobook_router, prefix="/api/audiobook")
app.include_router(raceroom_router)
app.include_router(replay_comparer_router, prefix="/api/replay_comparer")


@app.get("/")
async def root() -> dict:
    """Health‑check endpoint returning a simple JSON payload."""
    return {"message": "FastAPI server is running"}
