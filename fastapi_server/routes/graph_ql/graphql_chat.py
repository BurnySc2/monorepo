import asyncio
import time
from typing import AsyncGenerator, List, Optional, Set

import strawberry
from loguru import logger


@strawberry.type
class ChatMessage:
    id: int
    timestamp: int
    author: str
    message: str


# vvvv TODO refactor vvvvvvv
active_users: Set[str] = set()
chat_all_messages: List[ChatMessage] = []
chat_message_id = 0
queue_user_joined: asyncio.Queue[str] = asyncio.Queue()
queue_user_left: asyncio.Queue[str] = asyncio.Queue()
queue_new_message: asyncio.Queue[ChatMessage] = asyncio.Queue()
# ^^^^ TODO refactor ^^^^^^^


@strawberry.type
class ChatSystemQuery:
    @strawberry.field
    def chat_users(self) -> List[str]:
        return list(active_users)

    @strawberry.field
    def chat_messages(self) -> List[ChatMessage]:
        return chat_all_messages

    @strawberry.field
    def chat_hello(self) -> str:
        return 'hello'


@strawberry.type
class ChatSystemMutation:
    @strawberry.mutation
    def chat_join_room(self, username: str) -> bool:
        if username in active_users:
            return False
        active_users.add(username)
        queue_user_joined.put_nowait(username)
        return True

    @strawberry.mutation
    def chat_leave_room(self, username: str) -> Optional[bool]:
        if username in active_users:
            active_users.remove(username)
            queue_user_left.put_nowait(username)
            return True
        return False

    @strawberry.mutation
    def chat_send_message(self, username: str, message: str) -> int:
        """ Return id of the new chat message. """
        global chat_message_id
        chat_message_id += 1
        new_message = ChatMessage(
            id=chat_message_id,
            timestamp=int(time.time()),
            author=username,
            message=message,
        )  # type: ignore
        chat_all_messages.append(new_message)
        queue_new_message.put_nowait(new_message)
        return chat_message_id


@strawberry.type
class ChatSystemSubscription:
    @strawberry.subscription
    async def chat_user_joined(self) -> AsyncGenerator[str, None]:
        while 1:
            if queue_user_joined.empty():
                await asyncio.sleep(0.01)
            else:
                new_user = queue_user_joined.get_nowait()
                logger.info(f'new user: {new_user}')
                yield new_user

    @strawberry.subscription
    async def chat_user_left(self) -> AsyncGenerator[str, None]:
        while 1:
            if queue_user_left.empty():
                await asyncio.sleep(0.01)
            else:
                yield queue_user_left.get_nowait()

    @strawberry.subscription
    async def chat_new_message(self) -> AsyncGenerator[ChatMessage, None]:
        while 1:
            if queue_new_message.empty():
                await asyncio.sleep(0.01)
            else:
                yield queue_new_message.get_nowait()
