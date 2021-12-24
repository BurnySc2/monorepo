import contextlib
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
    session: Session = None  # type: ignore

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
    @contextlib.contextmanager
    def session_context(cls):
        """
        Used together with hypothesis: create a class-variable to be used in hypothesis. Unset once the test is over.
        Session strategy doesn't seem to work as expected, nor does setup example and teardown example with sql.
        """
        if cls.session is not None:
            # There's already another context manager running
            yield cls.session
        else:
            try:
                # cls.session = cls.create_file_sesssion()
                cls.session = cls.create_memory_sesssion()
                yield cls.session
            finally:
                if cls.session is not None:
                    db_path = pathlib.Path(TEST_DB_FILE_PATH)
                    # Remove file if it wasnt a memory database
                    if cls.session.bind.url.database != TEST_DB_MEMORY_PATH and db_path.is_file():
                        os.remove(db_path)
                    cls.session.close()
                    cls.session = None

    @classmethod
    @contextlib.contextmanager
    def client_context(cls):
        """ Same reasoning as above. """
        # See https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
        # https://strawberry.rocks/docs/integrations/fastapi#context_getter
        with cls.session_context() as _session:
            app.dependency_overrides[get_session] = cls.get_session
            client = TestClient(app)
            yield client

    @classmethod
    def get_session(cls) -> Session:
        assert isinstance(cls.session, Session)
        assert cls.session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
        return cls.session

    @classmethod
    def get_client(cls) -> TestClient:
        with cls.client_context() as client:
            return client

    @classmethod
    def get_schema(cls) -> strawberry.Schema:
        return schema

    @pytest.fixture(name='client_fixture')
    def client_fixture(self) -> TestClient:  # type: ignore
        with self.client_context() as client:
            yield client

    @pytest.fixture(name='session_fixture')
    def session_fixture(self) -> Session:  # type: ignore
        with self.session_context() as session:
            yield session

    @pytest.fixture(name='schema_fixture')
    def schema_fixture(self):
        yield self.get_schema()

    @classmethod
    def client_strategy(cls) -> SearchStrategy:
        return st.builds(cls.get_client)

    @classmethod
    def schema_strategy(cls) -> SearchStrategy:
        return st.builds(cls.get_schema)
