"""Entry point for the FastAPI server.

Provides a minimal FastAPI application that can be started via the
VS Code launch configuration added above.
"""

from fastapi import FastAPI

# Import and include routers from the existing Rio app setup
from routes.index import IndexRouter
from routes.login import login_router
from routes.replay_parser import replay_parser_router
from routes.tts_websocket import TTSRouter

app = FastAPI()


# Include the routers with appropriate prefixes
app.include_router(IndexRouter, prefix="/api")
app.include_router(login_router)
app.include_router(replay_parser_router, prefix="/api")
app.include_router(TTSRouter, prefix="/tts-api")


@app.get("/")
async def root() -> dict:
    """Health‑check endpoint returning a simple JSON payload."""
    return {"message": "FastAPI server is running"}
