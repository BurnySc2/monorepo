import hashlib
import os
import time
from typing import Optional

import jwt
from dotenv import load_dotenv
from loguru import logger
from strawberry.types import Info

load_dotenv()

if os.environ.get('JWT_ENCODE_SECRET', ''):
    logger.warning('ENV JWT_ENCODE_SECRET is not set')
SECRET = os.environ.get('JWT_ENCODE_SECRET', 'secret')

if len(os.environ.get('PASSWORD_HASH_SALT', '')) != 32:
    logger.warning('ENV PASSWORD_HASH_SALT is not set')
SALT: bytes = os.environ.get('PASSWORD_HASH_SALT', 'abcdefghijklmnopqrstuvwxyzABCDEF').encode()


def jwt_encode(data: dict, secret: str = SECRET) -> str:
    return jwt.encode(data, secret, algorithm='HS256')


def jwt_decode(token: str, secret: str = SECRET) -> dict:
    return jwt.decode(token, secret, algorithms=['HS256'])


def hash_password(password_plain: str, salt: bytes = SALT) -> str:
    return hashlib.pbkdf2_hmac('sha256', password_plain.encode(), salt=salt, iterations=10_000).hex()


def get_token_from_info(info: Info) -> Optional[str]:
    return info.context['request'].cookies.get('sessiontoken', None)


def token_is_valid(token: str, secret: str = SECRET) -> bool:
    data_from_token: dict = jwt_decode(token, secret=secret)
    assert isinstance(data_from_token, dict)
    assert 'expire_time' in data_from_token
    assert isinstance(data_from_token['expire_time'], float)
    assert 'username' in data_from_token
    assert isinstance(data_from_token['username'], str)
    return data_from_token.get('expire_time', -1) > time.time()


def token_is_valid_from_info(info: Info):
    session_token: Optional[str] = get_token_from_info(info)
    return session_token is not None and token_is_valid(session_token)


def get_username_from_token(token: str, secret: str = SECRET) -> str:
    # Assume it is a valid token
    return jwt_decode(token, secret=secret).get('username')  # type: ignore


def username_from_info(info: Info) -> Optional[str]:
    if token_is_valid_from_info(info):
        session_token = get_token_from_info(info)
        if session_token is not None:
            return get_username_from_token(session_token)
    return None


if __name__ == '__main__':
    data = {'bla': 'blubb'}
    token_example = jwt_encode(data)
    logger.info(f'{token_example=}')
    data_decoded = jwt_decode(token_example)
    logger.info(f'{data_decoded=}')

    logger.info(f'{hash_password("mypassword")=}')
