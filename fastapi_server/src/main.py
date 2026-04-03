"""Entry point for the FastAPI server.

Provides a minimal FastAPI application that can be started via the
VS Code launch configuration added above.
"""

import os
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from minio_helper import (
    GarageInit,
    bucket_create,
    get_s3_client,
)
from routes.index import IndexRouter
from routes.login import login_router
from routes.replay_parser import replay_parser_router
from routes.tts_websocket import TTSRouter
from routes.audiobook import audiobook_router

GARAGE_AUDIOBOOK_BUCKET = os.getenv("GARAGE_AUDIOBOOK_BUCKET", "garage-audiobook-bucket")
GARAGE_AUDIOBOOK_MAX_SIZE_MB = int(os.getenv("GARAGE_AUDIOBOOK_MAX_SIZE_MB", "100000"))
GARAGE_KEY_NAME = os.getenv("GARAGE_KEY_NAME", "audiobook-key")


async def init_garage() -> None:
    bucket_name = GARAGE_AUDIOBOOK_BUCKET
    max_size_bytes = GARAGE_AUDIOBOOK_MAX_SIZE_MB * 1024 * 1024

    async with get_s3_client() as s3:
        await bucket_create(s3, bucket_name)

    try:
        bucket_id = await GarageInit.bucket_id(bucket_name)
        if bucket_id is None:
            print(f"[init] Garage: bucket '{bucket_name}' created, quota not set (Admin API unavailable)")
        else:
            await GarageInit.set_quota(bucket_id, max_size_bytes)
            key = await GarageInit.create_key(GARAGE_KEY_NAME)
            await GarageInit.allow_bucket(key["accessKeyId"], bucket_id)
            print(f"[init] Garage: bucket={bucket_name}, key_id={key['accessKeyId']}")
    except (httpx.HTTPError, KeyError) as e:
        print(f"[init] Garage: bucket '{bucket_name}' created, skip quota/key setup ({type(e).__name__}: {e})")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_garage()
    yield


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


# Include the routers with appropriate prefixes
app.include_router(IndexRouter, prefix="/api")
app.include_router(login_router)
app.include_router(replay_parser_router, prefix="/api")
app.include_router(TTSRouter, prefix="/tts-api")
app.include_router(audiobook_router, prefix="/api/audiobook")


@app.get("/")
async def root() -> dict:
    """Health‑check endpoint returning a simple JSON payload."""
    return {"message": "FastAPI server is running"}
