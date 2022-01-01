from fastapi import Depends, Response
from fastapi.routing import APIRouter
from pydantic import BaseModel  # pylint: disable=E0611
from sqlmodel import Session, select
from starlette.responses import JSONResponse

from fastapi_server.database.database import get_session
from fastapi_server.models.user import User

login_router = APIRouter()


class LoginModel(BaseModel):
    email: str
    password: str


# TODO: Replace /login endpoint when Response is available in strawberry query info-context
@login_router.post('/login')
async def login(login_data: LoginModel, session: Session = Depends(get_session)) -> Response:
    statement = select(User).where(User.email == login_data.email, User.password_hashed == login_data.password)
    user = session.exec(statement).first()
    if user is None:
        raise FileNotFoundError('Email and password do not match')

    # Set message and cookies in frontend
    content = {'message': 'Come to the dark side, we have cookies'}
    response = JSONResponse(content=content)
    response.set_cookie(key='fakesession', value='fake-cookie-session-value', httponly=True, secure=True, expires=3600)
    return response
