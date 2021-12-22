import asyncio

import strawberry
from loguru import logger
from sqlmodel import Session, select
from strawberry.types import Info

from fastapi_server.database.database import get_session
from fastapi_server.models.user import User
from fastapi_server.routes.graph_ql.broadcaster import Broadcast, BroadcastEvent, Subscriber

broadcast = Broadcast()


@strawberry.type
class UserSystemQuery:
    @strawberry.field
    def user_login(self, info: Info, email: str, password: str) -> str:
        session: Session = info.context['session']
        # users = session.exec(select(User)).all()
        statement = select(User).where(User.email == email, User.password_hashed == password)
        user = session.exec(statement).first()
        if user is None:
            raise FileNotFoundError('Email and password do not match')
        return f'Login successful for {email}'


@strawberry.type
class UserSystemMutation:
    @strawberry.mutation
    def user_register(self, username: str, email: str, password: str, password_repeated: str) -> bool:
        if password != password_repeated:
            raise KeyError('not same pw')
        password_hashed = hash(password)
        with get_session() as session:
            session.add(
                User(
                    username=username,
                    email=email,
                    password_hashed=password_hashed,
                    is_admin=False,
                    is_disabled=False,
                    is_verified=False,
                )
            )
        return True


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
