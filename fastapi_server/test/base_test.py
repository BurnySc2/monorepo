import contextlib
from typing import Generator

import pytest
from starlette.testclient import TestClient

from main import app


class BaseTest:
    method_client: TestClient = None  # type: ignore

    def setup_method(self, _method):
        BaseTest.method_client = TestClient(app)

    def teardown_method(self, _method):
        BaseTest.method_client = None

    @classmethod
    @contextlib.contextmanager
    def method_client_context(cls):
        client = TestClient(app)
        try:
            yield client
        finally:
            cls.example_client = None

    @pytest.fixture(name='method_client_fixture')
    def method_client_fixture(self) -> Generator[TestClient, None, None]:
        with BaseTest.method_client_context() as client:
            assert isinstance(client, TestClient)
            yield client
