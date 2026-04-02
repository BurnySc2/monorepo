"""Entry point for the FastAPI server.

Provides a minimal FastAPI application that can be started via the
VS Code launch configuration added above.
"""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import and include routers from the existing Rio app setup
from routes.index import IndexRouter
from routes.login import login_router
from routes.replay_parser import replay_parser_router
from routes.tts_websocket import TTSRouter

app = FastAPI()

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


@app.get("/")
async def root() -> dict:
    """Health‑check endpoint returning a simple JSON payload."""
    return {"message": "FastAPI server is running"}
