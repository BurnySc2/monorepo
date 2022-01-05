import asyncio
import time
from collections import deque
from typing import AsyncGenerator, Deque, List, Set

import strawberry
from loguru import logger

from fastapi_server.routes.graph_ql.broadcaster import Broadcast, BroadcastEvent, Subscriber

broadcast = Broadcast()


@strawberry.type
class Event:
    timestamp: int
    data: str


@strawberry.type
class ChatMessage:
    timestamp: int
    author: str
    message: str


# vvvv TODO refactor vvvvvvv
# Users
active_users: Set[str] = set()
# Messages
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
    async def chat_join_room(self, username: str) -> bool:
        if username in active_users:
            # Disallow users to join twice with same nickname
            return False
        active_users.add(username)
        event = Event(
            timestamp=int(time.time()),
            data=username,
        )
        await broadcast.publish(channel='chat_user_joined', message=event)
        return True

    @strawberry.mutation
    async def chat_leave_room(self, username: str) -> bool:
        if username not in active_users:
            # Disallow users to chat who haven't joined
            return False
        active_users.remove(username)
        event = Event(
            timestamp=int(time.time()),
            data=username,
        )
        await broadcast.publish(channel='chat_user_left', message=event)
        return True

    @strawberry.mutation
    async def chat_send_message(self, username: str, message: str) -> bool:
        if username not in active_users:
            # Disallow users to chat who haven't joined
            return False
        new_message = ChatMessage(
            timestamp=int(time.time()),
            author=username,
            message=message,
        )
        # Store messages for new chatters
        messages.append(new_message)
        # Broadcast message to all subscribers
        await broadcast.publish(channel='chat_new_message', message=new_message)
        return True


@strawberry.type
class ChatSystemSubscription:

    @strawberry.subscription
    async def chat_user_joined(self) -> AsyncGenerator[Event, None]:
        subscriber: Subscriber
        async with broadcast.subscribe(channel='chat_user_joined') as subscriber:
            event: BroadcastEvent
            async for event in subscriber:
                yield event.message

    @strawberry.subscription
    async def chat_user_left(self) -> AsyncGenerator[Event, None]:
        subscriber: Subscriber
        async with broadcast.subscribe(channel='chat_user_left') as subscriber:
            event: BroadcastEvent
            async for event in subscriber:
                yield event.message

    @strawberry.subscription
    async def chat_new_message(self) -> AsyncGenerator[ChatMessage, None]:
        subscriber: Subscriber
        async with broadcast.subscribe(channel='chat_new_message') as subscriber:
            event: BroadcastEvent
            try:
                async for event in subscriber:
                    yield event.message
            finally:
                # logger.info('Unsubscribed')
                pass


async def main():
    subscriber: Subscriber
    async with broadcast.subscribe(channel='chat_new_message') as subscriber:
        logger.info('Subscribed')
        await subscriber.queue.put(None)
        event: BroadcastEvent
        async for event in subscriber:
            print(event)
    logger.info('Unsubscribed')


if __name__ == '__main__':
    asyncio.run(main())
