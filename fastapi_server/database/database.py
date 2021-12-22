import os

from dotenv import load_dotenv
from sqlmodel import Session, SQLModel, create_engine

load_dotenv()

DATABASE_PATH = os.environ.get('DATABASE_PATH')
# engine = create_engine('sqlite:///temp.db')
# engine = create_engine('sqlite:///:memory:')
engine = create_engine(DATABASE_PATH)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        return session
