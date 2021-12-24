from typing import Optional

from sqlmodel import Field, SQLModel


class TodoItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    todo_text: str
    created_timestamp: int
    done: bool = False
    done_timestamp: int = -1
