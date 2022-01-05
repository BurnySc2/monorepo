import os
import random
import time

from dotenv import load_dotenv
from fastapi import Depends, Response
from fastapi.routing import APIRouter
from loguru import logger
from pydantic import BaseModel  # pylint: disable=E0611
from sqlmodel import Session, select
from starlette.responses import JSONResponse

from fastapi_server.helper.database import get_session
from fastapi_server.helper.helper import hash_password, jwt_encode
from fastapi_server.models.user import User

login_router = APIRouter()

load_dotenv()

if os.environ.get('LOGIN_TOKEN_EXPIRE_TIME_SECONDS', '0') != '0':
    logger.warning('ENV LOGIN_TOKEN_EXPIRE_TIME_SECONDS is not set')
EXPIRE_TIME = int(os.environ.get('LOGIN_TOKEN_EXPIRE_TIME_SECONDS', '60'))


class LoginModel(BaseModel):
    email: str
    password: str


# TODO: Replace /login endpoint when Response is available in strawberry query info-context
@login_router.post('/login')
async def login(login_data: LoginModel, session: Session = Depends(get_session)) -> Response:
    statement = select(User).where(
        User.email == login_data.email, User.password_hashed == hash_password(login_data.password)
    )
    user = session.exec(statement).first()
    if user is None:
        raise FileNotFoundError('Email and password do not match')

    # Set message and cookies in frontend
    # TODO Change response message
    content = {'message': 'Come to the dark side, we have cookies'}
    response = JSONResponse(content=content)
    # TODO Replace secret with some env variable
    token_value = jwt_encode({
        'username': user.username,
        'expire_time': time.time() + EXPIRE_TIME,
    })
    response.set_cookie(
        key='sessiontoken',
        value=token_value,
        httponly=True,
        secure=True,
        expires=EXPIRE_TIME + random.randint(1, 3600)
    )
    return response
