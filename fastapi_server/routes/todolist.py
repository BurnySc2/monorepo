import time
from dataclasses import dataclass
from typing import Dict, List, Union

from fastapi import Depends, Request
from fastapi.routing import APIRouter
from loguru import logger
from sqlalchemy.sql import Delete
from sqlmodel import Session, delete, select

from fastapi_server.helper.database import get_session
from fastapi_server.models.todoitem import TodoItem

todo_list_router = APIRouter()


@todo_list_router.get('/api')
async def show_all_todos(session: Session = Depends(get_session)) -> List[Dict[str, Union[int, str]]]:
    items = session.exec(select(TodoItem)).all()
    logger.info([{key: value for key, value in item.__dict__.items() if not key.startswith('_')} for item in items])
    return [{key: value for key, value in item.__dict__.items() if not key.startswith('_')} for item in items]


@todo_list_router.post('/api/{todo_description}')
async def create_new_todo(todo_description: str, session: Session = Depends(get_session)):
    # https://fastapi.tiangolo.com/advanced/using-request-directly/
    if todo_description:
        logger.info(f'Attempting to insert new todo: {todo_description}')
        session.add(TodoItem(todo_text=todo_description, created_timestamp=int(time.time())))
        session.commit()


# Alternative to above with request body:
@todo_list_router.post('/api_body')
async def create_new_todo2(request: Request, session: Session = Depends(get_session)):
    """
    Example with accessing request body.
    Send a request with body {"new_todo": "<todo task description>"}
    """
    # https://fastapi.tiangolo.com/advanced/using-request-directly/
    request_body = await request.json()
    todo_item = request_body.get('new_todo', None)
    if todo_item:
        logger.info(f'Attempting to insert new todo: {todo_item}')
        session.add(TodoItem(todo_text=todo_item, created_timestamp=int(time.time())))
        session.commit()


@dataclass()
class Item:
    todo_description: str


# Alternative to above with model:
@todo_list_router.post('/api_model')
async def create_new_todo3(item: Item, session: Session = Depends(get_session)):
    """
    Example with accessing request body.
    Send a request with body {"todo_description": "<todo task description>"}
    """
    # https://fastapi.tiangolo.com/tutorial/body/#import-pydantics-basemodel
    logger.info(f'Received item: {item}')
    if item and item.todo_description:
        logger.info(f'Attempting to insert new todo: {item.todo_description}')
        session.add(TodoItem(todo_text=item.todo_description, created_timestamp=int(time.time())))
        session.commit()


@todo_list_router.delete('/api/{todo_id}')
async def remove_todo(todo_id: int, session: Session = Depends(get_session)) -> bool:
    """ Example of using /api/itemid with DELETE request """
    logger.info(f'Attempting to remove todo id: {todo_id}')
    statement: Delete = delete(TodoItem).where(TodoItem.id == todo_id)  # type: ignore
    result = session.exec(statement)  # type: ignore
    session.commit()
    return result.rowcount == 1
