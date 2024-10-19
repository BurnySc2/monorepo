"""
TTS for twitch streamers

- on websocket connection, connects to a twitch channel and creates a queue-worker
- on message in channel: check if tts name is in list of tts voices
    - add it to queue
- queue worker:
    - check if tts is playing
    - if empty, check for item in queue, process it, and play it
"""

from __future__ import annotations

import os
from typing import Annotated, Literal

from litestar import Controller, get, post
from litestar.enums import RequestEncodingType
from litestar.params import Body
from litestar.response import Template
from pydantic import BaseModel

from src.routes.tts.generate_tts import Voices, generate_tts

WS_BACKEND_SERVER_URL = os.getenv("BACKEND_WS_SERVER_URL", "ws:0.0.0.0:8000")


class TTSData(BaseModel):
    tts_voice: str
    tts_text: str


class MyTTSRoute(Controller):
    path = "/tts"
    VOICES_LIST: list[str] = [v.name for v in Voices]

    @get("/")
    async def index(
        self,
        volume: int = 100,
    ) -> Template:
        # Return an initial index.html that can play tts from input form
        return Template(
            template_name="tts/index.html",
            context={
                "voices": sorted(self.VOICES_LIST),
                "mp3_b64_data": "",
                "volume": volume / 100,
            },
        )

    @post("/generate_mp3")
    async def generate_mp3(
        self,
        data: Annotated[TTSData, Body(media_type=RequestEncodingType.URL_ENCODED)],
    ) -> Template:
        mp3_b64_data, _ = await generate_tts(Voices[data.tts_voice], data.tts_text)
        """
        Returns a template which allows you to create an audio from text
        """
        return Template(
            template_name="tts/new_audio.html",
            context={
                "mp3_b64_data": mp3_b64_data,
            },
        )

    # http://0.0.0.0:8000/tts/twitch/STREAMER_NAME?read_name_lang=none&volume=100
    # https://URL/tts/twitch/STREAMER_NAME?read_name_lang=none&volume=100
    @get("/twitch/{stream_name: str}")
    async def tts_overlay(
        self,
        stream_name: str,
        # Only allows these for 'read_name_lang'
        read_name_lang: Literal["none", "en", "de"] = "none",
        # Volume between 0 and 100
        volume: int = 100,
    ) -> Template:
        """
        Returns a template which connects to the websocket connection
        """
        # https://docs.litestar.dev/2/usage/websockets.html#interacting-with-the-websocket-directly
        return Template(
            template_name="tts/overlay_index.html",
            context={
                "ws_backend_server_url": WS_BACKEND_SERVER_URL,
                "stream_name": stream_name.lower(),
                "read_name_lang": read_name_lang,
                "volume": volume / 100,
            },
        )
