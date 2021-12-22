import os
import pathlib

import hypothesis.strategies as st
import pytest
import strawberry
from hypothesis.strategies import SearchStrategy
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from starlette.testclient import TestClient

from fastapi_server.database.database import get_session
from fastapi_server.main import app
from fastapi_server.routes.graphql import schema

TEST_DB_FILE_PATH = 'test.db'
TEST_DB_URL = f'sqlite:///{TEST_DB_FILE_PATH}'
TEST_DB_MEMORY_PATH = ':memory:'
TEST_DB_MEMORY_URL = f'sqlite:///{TEST_DB_MEMORY_PATH}'


class BaseTest:
    session: Session = None

    @classmethod
    def setup_method(cls):
        cls.setup_example()
        assert cls.session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}

    @classmethod
    def setup_example(cls):
        if cls.session is None:
            # cls.session = cls.create_file_sesssion()
            cls.session = cls.create_memory_sesssion()
            assert cls.session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}

    @classmethod
    def teardown_method(cls):
        cls.teardown_example()

    @classmethod
    def teardown_example(cls, _token=None):
        if cls.session is not None:
            db_path = pathlib.Path(TEST_DB_FILE_PATH)
            if cls.session.bind.url.database != TEST_DB_MEMORY_PATH and db_path.is_file():
                os.remove(db_path)
            cls.session.close()
            cls.session = None

    @classmethod
    def create_file_sesssion(cls):
        engine = create_engine(TEST_DB_URL, connect_args={'check_same_thread': False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(engine)
        with Session(engine, autoflush=False, autocommit=False) as session:
            return session

    @classmethod
    def create_memory_sesssion(cls):
        engine = create_engine(TEST_DB_MEMORY_URL, connect_args={'check_same_thread': False}, poolclass=StaticPool)
        SQLModel.metadata.create_all(engine)
        with Session(engine, autoflush=False, autocommit=False) as session:
            # Can this be "yield" instead?
            return session

    @classmethod
    def get_session(cls) -> Session:
        # Create session if not set
        if cls.session is None:
            cls.setup_example()
        assert cls.session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}
        # Can this be "yield" instead?
        return cls.session

    @classmethod
    def get_client(cls) -> TestClient:
        # See https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
        # https://strawberry.rocks/docs/integrations/fastapi#context_getter
        app.dependency_overrides[get_session] = cls.get_session
        client = TestClient(app)
        return client

    @classmethod
    def get_schema(cls) -> strawberry.Schema:
        return schema

    @pytest.fixture(name='session_fixture')
    def session_fixture(self) -> Session:
        yield self.get_session()

    @pytest.fixture(name='client_fixture')
    def client_fixture(self):
        yield self.get_client()

    @pytest.fixture(name='schema_fixture')
    def schema_fixture(self):
        yield self.get_schema()

    @classmethod
    def session_strategy(cls) -> SearchStrategy:
        return st.builds(cls.get_session)

    @classmethod
    def client_strategy(cls) -> SearchStrategy:
        return st.builds(cls.get_client)

    @classmethod
    def schema_strategy(cls) -> SearchStrategy:
        return st.builds(cls.get_schema)
