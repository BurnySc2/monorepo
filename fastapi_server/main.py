import sys
from pathlib import Path

# Be able to launch from root folder
sys.path.append(str(Path(__file__).parents[1]))

import asyncio
import os

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from fastapi_server.routes.chat import chat_router
from fastapi_server.routes.graphql import strawberry_router
from fastapi_server.routes.hello_world import background_task_function, hello_world_router
from fastapi_server.routes.todolist import create_database_if_not_exist, get_db, todo_list_router

ENV = os.environ.copy()

app = FastAPI()
app.include_router(hello_world_router)
app.include_router(chat_router)
app.include_router(todo_list_router)
app.include_router(strawberry_router)

origins = [
    'https://burnysc2.github.io',
] + [f'http://localhost:{i}' for i in range(1, 2**16)]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.on_event('startup')
async def startup_event():
    asyncio.create_task(background_task_function('hello', other_text=' world!'))
    create_database_if_not_exist()
    logger.info('Hello world!')


@app.on_event('shutdown')
def shutdown_event():
    db = get_db()
    if db():
        db.close()
    logger.info('Bye world!')


if __name__ == '__main__':
    uvicorn.run('__main__:app', host='0.0.0.0', port=8000, reload=True)
