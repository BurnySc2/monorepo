import json
import time
from dataclasses import dataclass, field
from typing import Dict, List

from dataclasses_json import DataClassJsonMixin
from fastapi.routing import APIRouter
from loguru import logger
from starlette.websockets import WebSocket, WebSocketDisconnect

from fastapi_server.helper.websocket_manager import Handler, WebsocketManager

chat_router = APIRouter()


@dataclass
class ChatMessage(DataClassJsonMixin):
    timestamp: float
    author: str
    message: str


@dataclass
class ChatManager(Handler):
    usernames: Dict[str, WebSocket] = field(default_factory=dict)
    messages_history: List[ChatMessage] = field(default_factory=list)

    # General helper functions
    @staticmethod
    async def send_json(message: Dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def send_message_history(self, websocket: WebSocket):
        await self.send_json({'message_history': [m.to_dict() for m in self.messages_history]}, websocket)

    async def disconnect_username(self, name: str = None, websocket: WebSocket = None) -> str:
        if name is not None:
            assert name in self.usernames
            self.usernames.pop(name)
        else:
            assert websocket
            for username, ws in self.usernames.items():
                if ws == websocket:
                    self.usernames.pop(username)
                    return username
        return ''

    # Main data handler
    async def handle_data(self, websocket_manager: WebsocketManager, websocket: WebSocket, data_json: dict):
        logger.info(f'Received data_json: {data_json}')
        if 'example' in data_json:
            # Example message from client on connect
            await self.on_example(message=data_json['example'], websocket=websocket)
        elif 'connect_user' in data_json:
            # Client is trying to join chat
            await self.on_connect_user(name=data_json['connect_user'], websocket=websocket)
        elif 'chat_message' in data_json:
            # Client wrote a message
            author = data_json['chat_message']['author']
            message = data_json['chat_message']['message']
            await self.on_chat_message(
                websocket_manager=websocket_manager, author=author, message=message, websocket=websocket
            )

    # EVENTS
    async def on_example(self, message: str, websocket: WebSocket):
        logger.info(f'Message from client was: {message}')
        await self.send_json({'message': 'Hello from server!'}, websocket)

    async def on_connect_user(self, name: str, websocket: WebSocket):
        logger.info(f'User is trying to connect with username: {name}')
        if name not in self.usernames:
            logger.info(f'Name was not yet taken! Accepting user: {name}')
            self.usernames[name] = websocket
            await self.send_json({'connect_user': name}, websocket)
            await self.send_message_history(websocket)
        else:
            await self.send_json({'error': 'username taken'}, websocket)

    async def on_chat_message(
        self, websocket_manager: WebsocketManager, author: str, message: str, websocket: WebSocket
    ):
        if author not in self.usernames or self.usernames[author] != websocket:
            return
        logger.info(f'Broadcasting new message from {author}: {message}')
        new_message = ChatMessage(
            timestamp=time.time(),
            author=author,
            message=message,
        )
        self.messages_history.append(new_message)
        message_to_send = {'new_message': new_message.to_dict()}
        for connection in websocket_manager.active_connections:
            try:
                await self.send_json(message_to_send, connection)
            except RuntimeError:
                # When does runtime error occur?
                await websocket_manager.disconnect(connection)


my_chat_manager = ChatManager()
my_websocket_manager = WebsocketManager(handler=my_chat_manager)


@chat_router.websocket('/chatws')
async def websocket_endpoint(websocket: WebSocket):
    await my_websocket_manager.connect(websocket)
    try:
        while 1:
            await my_websocket_manager.receive(websocket)
    except WebSocketDisconnect:
        await my_websocket_manager.disconnect(websocket)
        name = await my_chat_manager.disconnect_username(websocket=websocket)
        logger.info(f'Username disconnected: \'{name}\'')
