import os
from pathlib import Path

from dotenv import load_dotenv
from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

ROOT_FASTAPI_SERVER_PATH = Path(__file__).parents[1]
DATABASE_PATH = os.environ.get('DATABASE_PATH')
DATABASE_USE_MEMORY = os.environ.get('DATABASE_USE_MEMORY')
if DATABASE_PATH == ':memory:' or DATABASE_USE_MEMORY == 'TRUE':
    logger.info('Using memory database!')
    engine = create_engine('sqlite:///:memory:')
else:
    assert DATABASE_PATH is not None
    correct_path = ROOT_FASTAPI_SERVER_PATH / DATABASE_PATH
    # engine = create_engine('sqlite:///temp.db')
    # engine = create_engine('sqlite:///:memory:')
    logger.info(f'DB Path: {correct_path}')
    engine = create_engine(f'sqlite:///{correct_path.absolute().__str__()}')


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        return session
