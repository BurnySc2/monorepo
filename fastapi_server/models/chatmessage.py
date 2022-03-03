from typing import Optional

from sqlmodel import Field, SQLModel

from fastapi_server.models.user import User


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    timestamp: int
    message: str
    user_id: int = Field(foreign_key='user.id')
    user: User
