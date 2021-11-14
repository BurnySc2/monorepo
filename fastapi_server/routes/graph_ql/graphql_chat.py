import asyncio
import time
from collections import deque
from typing import AsyncGenerator, Deque, List, Optional, Set

import strawberry


@strawberry.type
class Event:
    id: int
    timestamp: int
    data: str


@strawberry.type
class ChatMessage:
    id: int
    timestamp: int
    author: str
    message: str


# vvvv TODO refactor vvvvvvv
# User joined, user left events
event_id = 0
active_users: Set[str] = set()
user_joined_events: List[Event] = []
user_left_events: List[Event] = []
# Messages
chat_message_id = 0
messages: Deque[ChatMessage] = deque()
# ^^^^ TODO refactor ^^^^^^^


@strawberry.type
class ChatSystemQuery:
    @strawberry.field
    def chat_users(self) -> List[str]:
        return list(active_users)

    @strawberry.field
    def chat_messages(self) -> List[ChatMessage]:
        return list(messages)

    @strawberry.field
    def chat_hello(self) -> str:
        return 'hello'


@strawberry.type
class ChatSystemMutation:
    @strawberry.mutation
    def chat_join_room(self, username: str) -> bool:
        global event_id
        if username in active_users:
            return False
        active_users.add(username)
        event = Event(
            id=event_id,
            timestamp=int(time.time()),
            data=username,
        )  # type: ignore
        event_id += 1
        user_joined_events.append(event)
        return True

    @strawberry.mutation
    def chat_leave_room(self, username: str) -> Optional[bool]:
        global event_id
        if username in active_users:
            active_users.remove(username)
            event = Event(
                id=event_id,
                timestamp=int(time.time()),
                data=username,
            )  # type: ignore
            event_id += 1
            user_left_events.append(event)
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
        messages.append(new_message)
        return chat_message_id


@strawberry.type
class ChatSystemSubscription:
    @strawberry.subscription
    async def chat_user_joined(self) -> AsyncGenerator[str, None]:
        index = len(user_joined_events)
        while 1:
            if len(user_joined_events) > index:
                new_user: Event = user_joined_events[index]
                index += 1
                yield new_user.data
            else:
                await asyncio.sleep(0.01)

    @strawberry.subscription
    async def chat_user_left(self) -> AsyncGenerator[str, None]:
        index = len(user_left_events)
        while 1:
            if len(user_left_events) > index:
                user_left: Event = user_left_events[index]
                index += 1
                yield user_left.data
            else:
                await asyncio.sleep(0.01)

    @strawberry.subscription
    async def chat_new_message(self) -> AsyncGenerator[ChatMessage, None]:
        index = len(messages)
        while 1:
            if len(messages) > index:
                new_message = messages[index]
                index += 1
                yield new_message
            else:
                await asyncio.sleep(0.01)
