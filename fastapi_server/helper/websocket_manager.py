from __future__ import annotations

import json
from dataclasses import dataclass, field

from loguru import logger
from starlette.websockets import WebSocket


class Handler:

    async def handle_data(self, websocket_manager: WebsocketManager, websocket: WebSocket, data_json: dict):
        raise NotImplementedError()


@dataclass
class WebsocketManager:
    active_connections: list[WebSocket] = field(default_factory=list)
    handler: Handler = field(default_factory=Handler)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def receive(self, websocket: WebSocket):
        data = await websocket.receive_text()
        try:
            data_json = json.loads(data)
        except json.JSONDecodeError:
            logger.error(f'Could not process data: {data}')
            return
        await self.handler.handle_data(websocket_manager=self, websocket=websocket, data_json=data_json)
