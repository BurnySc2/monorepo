import os
import sqlite3
from pathlib import Path
from typing import Optional

from loguru import logger

# pylint: disable=E0611
from pydantic import BaseModel

db: Optional[sqlite3.Connection] = None


# pylint: disable=R0903
class TodoItem(BaseModel):
    todo_description: str


def create_database_if_not_exist():
    # pylint: disable=W0603
    global db
    todos_db = Path(__file__).parent.parent / 'data' / 'todos.db'
    logger.info(todos_db)
    if not todos_db.is_file():
        os.makedirs(todos_db.parent, exist_ok=True)
        db = sqlite3.connect(todos_db)
        db.execute('CREATE TABLE todos (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT)')
        db.commit()
        logger.info(f'Created new database: {todos_db.name}')
    else:
        db = sqlite3.connect(todos_db)
