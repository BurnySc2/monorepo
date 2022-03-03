from typing import Optional

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    # Why cant i use pydantic EmailStr here?
    email: str
    password_hashed: str
    is_admin: bool
    is_disabled: bool
    is_verified: bool
    # chat_messages: List["ChatMessage"] = Relationship(back_populates="user")
