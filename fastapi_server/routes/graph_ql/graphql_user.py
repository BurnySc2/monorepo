import asyncio

import strawberry
from sqlmodel import Session, select
from strawberry.types import Info

from fastapi_server.models.user import User
from fastapi_server.routes.graph_ql.broadcaster import Broadcast

broadcast = Broadcast()


@strawberry.type
class UserSystemQuery:
    @strawberry.field
    def user_login(self, info: Info, email: str, password: str) -> str:
        # TODO Replace with actual password hash function
        session: Session = info.context['session']
        statement = select(User).where(User.email == email, User.password_hashed == password)
        user = session.exec(statement).first()
        if user is None:
            raise FileNotFoundError('Email and password do not match')
        return f'Login successful for {email}'


@strawberry.type
class UserSystemMutation:
    @strawberry.mutation
    def user_register(self, info: Info, username: str, email: str, password: str, password_repeated: str) -> bool:
        if password != password_repeated:
            raise KeyError('not same pw')
        # TODO Replace with actual password hash function
        password_hashed = hash(password)
        session: Session = info.context['session']
        username_taken = session.exec(select(User).where(User.username == username)).first()
        if username_taken is not None:
            raise KeyError('username taken')
        email_taken = session.exec(select(User).where(User.email == email)).first()
        if email_taken is not None:
            raise KeyError('email taken')
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
        session.commit()
        return True

    @strawberry.mutation
    def user_send_password_reset_email(self, info: Info, email: str) -> bool:
        # Check if email exists in db, send password reset with token
        pass

    @strawberry.mutation
    def user_reset_password(self, info: Info, token: str) -> bool:
        # Decypher email from token, if token is valid reset password and send a generated password per email
        pass


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())
