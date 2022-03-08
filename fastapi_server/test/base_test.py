import contextlib

import pytest
from starlette.testclient import TestClient

from fastapi_server.main import app


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
    def method_client_fixture(self) -> TestClient:  # type: ignore
        with BaseTest.method_client_context() as client:
            assert isinstance(client, TestClient)
            yield client
