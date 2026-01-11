import asyncio
import os
from typing import Literal

from fastapi import APIRouter, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from loguru import logger

from rio_app.components.tts.irc_bot_async import IRCClient, ReadNameLang
from rio_app.components.tts.websocket_handler import TTSQueue, TTSQueueRunner

TTSRouter = APIRouter()

WS_BACKEND_SERVER_URL = os.getenv("BACKEND_WS_SERVER_URL", "ws:0.0.0.0:8000")


templates = Jinja2Templates(directory="templates")


# http://0.0.0.0:8000/tts/twitch/STREAMER_NAME?read_name_lang=none&volume=100
# https://URL/tts/twitch/STREAMER_NAME?read_name_lang=none&volume=100
@TTSRouter.get("/twitch/{stream_name}", response_class=HTMLResponse)
async def tts_overlay(
    request: Request,
    stream_name: str,
    # Only allows these for 'read_name_lang'
    read_name_lang: Literal["none", "en", "de"] = "none",
    # Volume between 0 and 100
    volume: int = 100,
):
    """
    Returns a template which connects to the websocket connection
    """
    # https://fastapi.tiangolo.com/advanced/templates/#using-jinja2templates
    return templates.TemplateResponse(
        request=request,
        name="tts/overlay_index.html",
        context={
            "ws_backend_server_url": WS_BACKEND_SERVER_URL,
            "stream_name": stream_name.lower(),
            "read_name_lang": read_name_lang,
            "volume": volume / 100,
        },
    )


@TTSRouter.websocket("/ws/{stream_name}/{read_name_lang}")
async def websocket_endpoint(websocket: WebSocket, stream_name: str, read_name_lang: ReadNameLang):
    """
    On new ws-connection:
        - join twitch channel
        - create worker that checks for new items in queue
    """
    await websocket.accept()

    # Initialize text queue if not exists
    if (stream_name, read_name_lang) not in TTSQueue.text_queue:
        TTSQueue.text_queue[(stream_name, read_name_lang)] = asyncio.Queue()
        # Create worker for this 'stream_name' and 'read_name_lang'
        asyncio.create_task(TTSQueueRunner(stream_name, read_name_lang).run())

    # Add socket - needs to happen after text_queue is initialized
    TTSQueue.add_websocket(stream_name, read_name_lang, websocket)

    # Start irc bot: listen to messages in channel
    if (stream_name, read_name_lang) not in TTSQueue.twitch_irc_bots:
        new_irc_client = IRCClient(
            channel=stream_name, read_name_lang=read_name_lang, callback=TTSQueue.irc_client_add_text_method
        )
        TTSQueue.twitch_irc_bots[(stream_name, read_name_lang)] = new_irc_client
        await new_irc_client.connect()
        # Keep irc bot running
        asyncio.create_task(new_irc_client.listen())

    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message text was: {data}")
    except WebSocketDisconnect:
        await TTSQueue.remove_ws(websocket, stream_name, read_name_lang)
    except Exception as e:  # noqa: BLE001
        logger.info(f"Unexpected error: {e}")
