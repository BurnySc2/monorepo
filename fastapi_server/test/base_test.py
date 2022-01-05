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

from fastapi_server.helper.database import get_session
from fastapi_server.main import app
from fastapi_server.routes.graphql import schema

TEST_DB_FILE_PATH = 'test.db'
TEST_DB_URL = f'sqlite:///{TEST_DB_FILE_PATH}'
TEST_DB_MEMORY_PATH = ':memory:'
TEST_DB_MEMORY_URL = f'sqlite:///{TEST_DB_MEMORY_PATH}'


class BaseTest:
    method_client: TestClient = None  # type: ignore
    method_session: Session = None  # type: ignore
    example_client: TestClient = None  # type: ignore
    example_session: Session = None  # type: ignore

    def setup_method(self, _method):
        BaseTest.method_session = BaseTest.create_memory_sesssion()
        # BaseTest.method_session = BaseTest.create_file_sesssion()
        BaseTest.method_client = TestClient(app)
        BaseTest.method_client.app.dependency_overrides[get_session] = BaseTest.method_get_session

    def teardown_method(self, _method):
        if BaseTest.method_session is not None:
            db_path = pathlib.Path(TEST_DB_FILE_PATH)
            # Remove file if it wasnt a memory database
            if BaseTest.method_session.bind.url.database != TEST_DB_MEMORY_PATH and db_path.is_file():
                os.remove(db_path)
            BaseTest.method_session.close()
            BaseTest.method_session = None
        app.dependency_overrides.clear()
        BaseTest.method_client = None

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
    def example_session_context(cls):
        """
        Used together with hypothesis: create a class-variable to be used in hypothesis. Unset once the test is over.
        Session strategy doesn't seem to work as expected, nor does setup example and teardown example with sql.
        """
        assert not isinstance(cls.example_session, Session)
        try:
            # cls.example_session = cls.create_file_sesssion()
            cls.example_session = cls.create_memory_sesssion()
            yield cls.example_session
        finally:
            if cls.example_session is not None:
                db_path = pathlib.Path(TEST_DB_FILE_PATH)
                # Remove file if it wasnt a memory database
                if cls.example_session.bind.url.database != TEST_DB_MEMORY_PATH and db_path.is_file():
                    os.remove(db_path)
                cls.example_session.close()
                cls.example_session = None

    @classmethod
    @contextlib.contextmanager
    def method_client_context(cls):
        """ Same reasoning as above. """
        # See https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
        # https://strawberry.rocks/docs/integrations/fastapi#context_getter
        # app.dependency_overrides.clear()
        app.dependency_overrides[get_session] = cls.method_get_session
        cls.method_client = TestClient(app)
        try:
            yield cls.method_client
        finally:
            cls.method_client = None
            app.dependency_overrides.clear()

    @classmethod
    @contextlib.contextmanager
    def example_client_context(cls):
        """ Same reasoning as above. """
        # See https://sqlmodel.tiangolo.com/tutorial/fastapi/tests/#pytest-fixtures
        # https://strawberry.rocks/docs/integrations/fastapi#context_getter
        with cls.example_session_context() as _session:
            app.dependency_overrides[get_session] = cls.example_get_session
            cls.example_client = TestClient(app)
            try:
                yield cls.example_client
            finally:
                cls.example_client = None
                app.dependency_overrides.clear()

    @classmethod
    def method_get_session(cls) -> Session:  # type: ignore
        assert isinstance(cls.method_session, Session)
        assert cls.method_session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
        yield cls.method_session

    @classmethod
    def example_get_session(cls) -> Session:  # type: ignore
        assert isinstance(cls.example_session, Session)
        assert cls.example_session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
        yield cls.example_session

    @classmethod
    def example_get_client(cls) -> TestClient:  # type: ignore
        yield cls.example_client

    @pytest.fixture(name='method_client_fixture')
    def method_client_fixture(self) -> TestClient:  # type: ignore
        with BaseTest.method_client_context() as client:
            assert isinstance(client, TestClient)
            yield client

    @pytest.fixture(name='example_client_fixture')
    def example_client_fixture(self) -> TestClient:  # type: ignore
        assert isinstance(BaseTest.example_client, TestClient)
        yield self.example_client

    @pytest.fixture(name='method_session_fixture')
    def method_session_fixture(self) -> Session:  # type: ignore
        assert isinstance(BaseTest.method_session, Session)
        yield BaseTest.method_session

    @pytest.fixture(name='example_session_fixture')
    def example_session_fixture(self) -> Session:  # type: ignore
        assert isinstance(BaseTest.example_session, Session)
        yield BaseTest.example_session

    @classmethod
    def get_schema(cls) -> strawberry.Schema:
        return schema

    @pytest.fixture(name='schema_fixture')
    def schema_fixture(self):
        return BaseTest.get_schema()

    @classmethod
    def schema_strategy(cls) -> SearchStrategy:
        """ Deprecated? """
        return st.builds(cls.get_schema)
