import hashlib
import os

import jwt
from dotenv import load_dotenv
from loguru import logger

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


if __name__ == '__main__':
    data = {'bla': 'blubb'}
    token_example = jwt_encode(data)
    logger.info(f'{token_example=}')
    data_decoded = jwt_decode(token_example)
    logger.info(f'{data_decoded=}')

    logger.info(f'{hash_password("mypassword")=}')
