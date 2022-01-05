import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from fastapi_server.helper.database import get_session, init_db
from fastapi_server.helper.helper import hash_password
from fastapi_server.models.user import User
from fastapi_server.routes.chat import chat_router
from fastapi_server.routes.graphql import strawberry_router
from fastapi_server.routes.hello_world import hello_world_router
from fastapi_server.routes.login import login_router
from fastapi_server.routes.todolist import todo_list_router

app = FastAPI()
app.include_router(hello_world_router)
app.include_router(chat_router)
app.include_router(todo_list_router)
app.include_router(strawberry_router)
app.include_router(login_router)

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
    # asyncio.create_task(background_task_function('hello', other_text=' world!'))
    # TODO: This init_db should probably not be in here, use alembic instead
    init_db()
    session = get_session()
    # Add admin user
    user = session.exec(session.query(User).where(User.username == 'admin')).first()
    if not user:
        session.add(
            User(
                username='admin',
                email='admin',
                password_hashed=hash_password('admin'),
                is_admin=True,
                is_disabled=False,
                is_verified=True,
            )
        )
        session.commit()
    # Add normal user
    user = session.exec(session.query(User).where(User.username == 'user')).first()
    if not user:
        session.add(
            User(
                username='user',
                email='user',
                password_hashed=hash_password('user'),
                is_admin=False,
                is_disabled=False,
                is_verified=True,
            )
        )
        session.commit()
    logger.info('Hello world!')


@app.on_event('shutdown')
def shutdown_event():
    logger.info('Bye world!')


if __name__ == '__main__':
    uvicorn.run('__main__:app', host='0.0.0.0', port=8000, reload=True)
