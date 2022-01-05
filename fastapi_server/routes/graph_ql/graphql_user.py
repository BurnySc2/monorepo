import asyncio
import time
from typing import Dict, Optional

import strawberry
from sqlmodel import Session, select
from strawberry.types import Info

from fastapi_server.helper.helper import hash_password, token_is_valid_from_info, username_from_info
from fastapi_server.models.user import User

# Limit password reset to once per day {account_id: last_sent_timestamp}
USER_PASSWORD_RESET: Dict[int, float] = {}
LIMIT_PASSWORD_RESET_SECONDS = 60 * 60 * 24  # once a day


@strawberry.type
class UserSystemQuery:
    # TODO Unused, currently this is an endpoint in login.py
    # @strawberry.field
    # def user_login(self, info: Info, email: str, password_plain: str) -> str:
    #     session: Session = info.context['session']
    #     statement = select(User).where(User.email == email, User.password_hashed == hash_password(password_plain))
    #     user = session.exec(statement).first()
    #     if user is None:
    #         raise FileNotFoundError('Email and password do not match')
    #     return f'Login successful for {email}'

    @strawberry.field
    def user_check_logged_in(self, info: Info) -> bool:
        # Read request cookies to check if user is logged in. Also check if the token in the cookie is valid
        return token_is_valid_from_info(info)

    @strawberry.field
    def user_get_username_from_token(self, info: Info) -> Optional[str]:
        # Read request cookies to check which username the token is valid for
        return username_from_info(info)


@strawberry.type
class UserSystemMutation:

    @strawberry.mutation
    def user_register(self, info: Info, username: str, email: str, password: str, password_repeated: str) -> bool:
        if password != password_repeated:
            raise KeyError('not same pw')
        # TODO Replace with actual password hash function
        password_hashed = hash_password(password)
        session: Session = info.context['session']
        username_taken = session.exec(select(User).where(User.username == username)).first()
        if username_taken is not None:
            raise KeyError('username taken')
        email_taken = session.exec(select(User).where(User.email == email)).first()
        if email_taken is not None:
            raise KeyError('email taken')
        # TODO Only add account after verification link has been clicked?
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
        # Send verification email
        return True

    @strawberry.mutation
    def user_send_password_reset_email(self, info: Info, email: str) -> str:
        # Check if email exists in db, send password reset with token
        session: Session = info.context['session']
        statement = select(User).where(User.email == email)
        user = session.exec(statement).first()
        if user is not None:
            user_id: int = user.id  # type: ignore
            last_reset: float = USER_PASSWORD_RESET.get(user_id, 0)
            last_reset_long_ago: bool = time.time() < last_reset + LIMIT_PASSWORD_RESET_SECONDS
            if user is not None and last_reset_long_ago:
                USER_PASSWORD_RESET[user_id] = time.time()
                # TODO: Send email with password reset link with token in it
            # Return this reponse regardless, to not allow users to figure out which emails have been taken.
        return f"A link to reset your password has been sent to '{email}'."

    @strawberry.mutation
    def user_reset_password(self, info: Info, token: str) -> bool:
        # Decypher email from token, if token is valid reset password and send a generated password per email
        pass


async def main():
    pass


if __name__ == '__main__':
    asyncio.run(main())
