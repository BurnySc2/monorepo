import os
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import Request
from fastapi.routing import APIRouter
from loguru import logger

ENV = os.environ.copy()
USE_MONGO_DB: bool = ENV.get('USE_MONGO_DB', 'True') == 'True'
USE_POSTGRES_DB: bool = ENV.get('USE_POSTGRES_DB', 'True') == 'True'
USE_LOCAL_SQLITE_DB: bool = ENV.get('USE_LOCAL_SQLITE_DB', 'True') == 'True'
SQLITE_FILENAME: str = ENV.get('SQLITE_FILENAME', 'todos.db')
# TODO use different database tables when using stage = dev/staging/prod


def set_sqlite_filename(file_name: str):
    global SQLITE_FILENAME
    SQLITE_FILENAME = file_name


todo_list_router = APIRouter()
db: Optional[sqlite3.Connection] = None

# TODO Communicate with postgresql and mongodb


def get_db() -> Optional[sqlite3.Connection]:
    return db


def create_database_if_not_exist():
    # pylint: disable=W0603
    global db
    todos_db = Path(__file__).parents[1] / 'data' / SQLITE_FILENAME
    if not todos_db.is_file():
        os.makedirs(todos_db.parent, exist_ok=True)
        db = sqlite3.connect(todos_db)
        db.execute('CREATE TABLE todos (id INTEGER PRIMARY KEY AUTOINCREMENT, task TEXT)')
        db.commit()
        logger.info(f'Created new database: {todos_db.name}')
    else:
        db = sqlite3.connect(todos_db)


@todo_list_router.get('/api')
async def show_all_todos() -> List[Dict[str, str]]:
    create_database_if_not_exist()
    todos = []
    if db:
        for row in db.execute('SELECT id, task FROM todos'):
            todos.append({
                'id': row[0],
                'content': row[1],
            })
    return todos


@todo_list_router.post('/api/{todo_description}')
async def create_new_todo(todo_description: str):
    # https://fastapi.tiangolo.com/advanced/using-request-directly/
    create_database_if_not_exist()
    if todo_description:
        logger.info(f'Attempting to insert new todo: {todo_description}')
        if db:
            db.execute('INSERT INTO todos (task) VALUES (?)', [todo_description])
            db.commit()


# Alternative to above with request body:
@todo_list_router.post('/api_body')
async def create_new_todo2(request: Request):
    """
    Example with accessing request body.
    Send a request with body {"new_todo": "<todo task description>"}
    """
    # https://fastapi.tiangolo.com/advanced/using-request-directly/
    create_database_if_not_exist()
    request_body = await request.json()
    todo_item = request_body.get('new_todo', None)
    if todo_item:
        logger.info(f'Attempting to insert new todo: {todo_item}')
        if db:
            db.execute('INSERT INTO todos (task) VALUES (?)', [todo_item])
            db.commit()


@dataclass()
class Item:
    todo_description: str


# Alternative to above with model:
@todo_list_router.post('/api_model')
async def create_new_todo3(item: Item):
    """
    Example with accessing request body.
    Send a request with body {"todo_description": "<todo task description>"}
    """
    # https://fastapi.tiangolo.com/tutorial/body/#import-pydantics-basemodel
    create_database_if_not_exist()
    logger.info(f'Received item: {item}')
    if item and item.todo_description:
        logger.info(f'Attempting to insert new todo: {item.todo_description}')
        if db:
            db.execute('INSERT INTO todos (task) VALUES (?)', [item.todo_description])
            db.commit()


@todo_list_router.delete('/api/{todo_id}')
async def remove_todo(todo_id: int):
    """ Example of using /api/itemid with DELETE request """
    create_database_if_not_exist()
    logger.info(f'Attempting to remove todo id: {todo_id}')
    if db:
        db.execute('DELETE FROM todos WHERE id==(?)', [todo_id])
        db.commit()
