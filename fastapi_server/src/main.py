"""Entry point for the FastAPI server.

Provides a minimal FastAPI application that can be started via the
VS Code launch configuration added above.
"""

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from components.audiobook.epub_reader import ensure_nltk_data
from routes.audiobook import audiobook_router
from routes.index import IndexRouter
from routes.login import login_router
from routes.raceroom import raceroom_router
from routes.replay_comparer import replay_comparer_router
from routes.replay_parser import replay_parser_router
from routes.telegram_browser import telegram_browser_router
from routes.tts_generate import tts_generate_router
from routes.tts_websocket import TTSRouter
from s3_helper import initialize_rustfs
from settings import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await initialize_rustfs()
    try:
        ensure_nltk_data()
    except (LookupError, OSError, RuntimeError):
        logger.warning("NLTK data unavailable at startup; continuing without it", exc_info=True)
    yield


# Use default JSONResponse to keep Pydantic Rust dump_json fastpath.
# default_response_class=ORJSONResponse is deprecated and disables the fastpath,
# while websocket_handler.send_mp3_data_to_ws keeps direct orjson usage.
app = FastAPI(lifespan=lifespan)

# Enable CORS
if settings.stage == "dev":
    # Allow the Svelte dev server to talk to the API
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https?://localhost:\d+",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
elif settings.stage == "prod":
    # Production CORS origins
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=r"https://[\w-]+\.burnysc2\.xyz|https://burnysc2\.xyz",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    # No CORS middleware outside dev/prod (e.g. test). Fail-closed by default;
    # frontend must use same-origin in these stages.
    logger.warning(f"No CORS middleware configured for STAGE={settings.stage!r}; same-origin only")


# Include the routers with appropriate prefixes
app.include_router(IndexRouter, prefix="/api")
app.include_router(login_router)
app.include_router(replay_parser_router, prefix="/api")
app.include_router(TTSRouter, prefix="/tts-api")
app.include_router(tts_generate_router, prefix="/tts-generate")
app.include_router(audiobook_router, prefix="/api/audiobook")
app.include_router(raceroom_router)
app.include_router(replay_comparer_router, prefix="/api/replay_comparer")
app.include_router(telegram_browser_router, prefix="/telegram-browser")


@app.get("/")
async def root() -> dict:
    """Health‑check endpoint returning a simple JSON payload."""
    return {"message": "FastAPI server is running"}


@app.get("/health")
async def health() -> dict:
    """Liveness probe for Docker / compose healthchecks.

    Liveness-only: always returns ok without checking DB/S3. Use /ready for readiness.
    """
    return {"status": "ok"}


@app.get("/ready")
async def ready() -> dict:
    """Readiness probe: pings DB and S3, 503 when unavailable.

    Liveness (/health) stays cheap for Docker; readiness is for load-balancer checks.
    """
    try:
        from schemas.audiobook.db_models import AudiobookBook

        await asyncio.wait_for(AudiobookBook.count(), timeout=2.0)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Readiness DB check failed: {e}")
        raise HTTPException(status_code=503, detail="DB not ready") from e
    try:
        from s3_helper import get_s3_client

        async def _ping_s3() -> None:
            async with get_s3_client() as s3:
                await s3.list_buckets()

        await asyncio.wait_for(_ping_s3(), timeout=2.0)
    except Exception as e:  # noqa: BLE001
        logger.warning(f"Readiness S3 check failed: {e}")
        raise HTTPException(status_code=503, detail="S3 not ready") from e
    return {"status": "ready"}
