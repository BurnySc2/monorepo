import time
from dataclasses import dataclass
from typing import List

from fastapi import Request
from fastapi.routing import APIRouter
from loguru import logger

todo_list_router = APIRouter()


@dataclass
class TodoItem:
    id: int
    todo_text: str
    created_timestamp: float
    done_timestamp: float
    done: bool


TODO_COUNTER = 0
TODOS: List[TodoItem] = []


@todo_list_router.get('/api')
async def show_all_todos() -> List[TodoItem]:
    # pylint: disable=W0602
    return TODOS


@todo_list_router.post('/api/{todo_description}')
async def create_new_todo(todo_description: str):
    # https://fastapi.tiangolo.com/advanced/using-request-directly/
    # pylint: disable=W0602
    global TODOS, TODO_COUNTER
    TODO_COUNTER += 1
    TODOS.append(
        TodoItem(
            id=TODO_COUNTER,
            todo_text=todo_description,
            created_timestamp=time.time(),
            done_timestamp=-1,
            done=False,
        )
    )


# Alternative to above with request body:
@todo_list_router.post('/api_body')
async def create_new_todo2(request: Request):
    """
    Example with accessing request body.
    Send a request with body {"new_todo": "<todo task description>"}
    """
    # https://fastapi.tiangolo.com/advanced/using-request-directly/
    # pylint: disable=W0602
    global TODOS, TODO_COUNTER
    request_body = await request.json()
    todo_item = request_body.get('new_todo', None)
    if todo_item:
        TODO_COUNTER += 1
        TODOS.append(
            TodoItem(
                id=TODO_COUNTER,
                todo_text=todo_item,
                created_timestamp=time.time(),
                done_timestamp=-1,
                done=False,
            )
        )


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
    # pylint: disable=W0602
    global TODOS, TODO_COUNTER
    logger.info(f'Received item: {item}')
    if item and item.todo_description:
        TODO_COUNTER += 1
        TODOS.append(
            TodoItem(
                id=TODO_COUNTER,
                todo_text=item.todo_description,
                created_timestamp=time.time(),
                done_timestamp=-1,
                done=False,
            )
        )


@todo_list_router.delete('/api/{todo_id}')
async def remove_todo(todo_id: int) -> bool:
    """ Example of using /api/itemid with DELETE request """
    # pylint: disable=W0603
    global TODOS
    logger.info(f'Attempting to remove todo id: {todo_id}')
    count_before = len(TODOS)
    TODOS = [item for item in TODOS if item.id != todo_id]
    count_after = len(TODOS)
    return count_after - count_before == 1
