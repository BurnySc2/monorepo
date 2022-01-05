import json
import time
from dataclasses import dataclass
from typing import Dict, List

from dataclasses_json import DataClassJsonMixin
from fastapi import WebSocket
from fastapi.routing import APIRouter
from loguru import logger
from starlette.websockets import WebSocketDisconnect

chat_router = APIRouter()


@dataclass
class ChatMessage(DataClassJsonMixin):
    timestamp: float
    author: str
    message: str


class WebsocketChatManager:

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.usernames: Dict[str, WebSocket] = {}
        self.messages_history: List[ChatMessage] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        await websocket.send_text(message)

    @staticmethod
    async def send_personal_json(message: Dict, websocket: WebSocket):
        await websocket.send_text(json.dumps(message))

    async def broadcast_new_message(self, message: ChatMessage):
        self.messages_history.append(message)
        message_to_send = {'newMessage': message.to_dict()}
        for connection in self.active_connections:
            try:
                await self.send_personal_json(message_to_send, connection)
            except RuntimeError:
                await self.disconnect(connection)

    def name_taken(self, name: str) -> bool:
        return name in self.usernames

    def verify(self, name: str, websocket: WebSocket) -> bool:
        return name in self.usernames and self.usernames[name] == websocket

    async def connect_username(self, name: str, websocket: WebSocket):
        assert name not in self.usernames
        self.usernames[name] = websocket
        await self.send_personal_json({'connectUser': name}, websocket)
        await self.send_message_history(websocket)

    async def send_message_history(self, websocket: WebSocket):
        await self.send_personal_json({'newMessageHistory': [m.to_dict() for m in self.messages_history]}, websocket)

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


websocket_chat_manager = WebsocketChatManager()


@chat_router.websocket('/chatws')
async def websocket_endpoint(websocket: WebSocket):
    await websocket_chat_manager.connect(websocket)
    try:
        while 1:
            data = await websocket.receive_text()
            data_json = json.loads(data)
            if 'message' in data_json:
                # Example message from client on connect
                message = data_json['message']
                logger.info(f'Message from client was: {message}')
                await websocket_chat_manager.send_personal_json({'message': 'Hello from server!'}, websocket)
            elif 'tryToConnectUser' in data_json:
                # Client is trying to join chat
                name = data_json['tryToConnectUser']
                logger.info(f'User is trying to connect with username: {name}')
                if not websocket_chat_manager.name_taken(name):
                    logger.info(f'Name was not yet taken! Accepting user: {name}')
                    await websocket_chat_manager.connect_username(name, websocket)

                else:
                    await websocket_chat_manager.send_personal_json({'error': 'usernameTaken'}, websocket)
            elif 'sendChatMessage' in data_json:
                # Client wrote a message
                message_data = data_json['sendChatMessage']
                author = message_data['author']
                if websocket_chat_manager.verify(author, websocket):
                    message = message_data['message']
                    logger.info(f'Broadcasting new message from {author}: {message}')
                    await websocket_chat_manager.broadcast_new_message(
                        ChatMessage(
                            # timestamp=message_data["timestamp"],
                            timestamp=time.time(),
                            author=author,
                            message=message,
                        ),
                    )

    except WebSocketDisconnect:
        await websocket_chat_manager.disconnect(websocket)
        name = await websocket_chat_manager.disconnect_username(websocket=websocket)
        logger.info(f'Username disconnected: {name}!')
