import asyncio
import os
import time
from collections.abc import Iterator
from contextlib import suppress

import pytest
from litestar import Litestar
from litestar.testing import TestClient
from minio import Minio, S3Error
from piccolo.table import Table, create_db_tables, drop_db_tables
from piccolo.utils.sync import run_sync
from pytest_httpx import HTTPXMock
from routes.audiobook.my_minio_client import minio_check_if_object_exists
from routes.login_logout import COOKIES

from _app import app
from models.audiobook import AudiobookBook, AudiobookChapter

TABLES: list[type[Table]] = [AudiobookBook, AudiobookChapter]


async def helper_wait_till_minio_object_exists(bucket_name: str, object_name: str, max_wait_seconds: float = 5) -> bool:
    # Sleep till bucket object exists
    time_start = time.time()
    while time.time() - time_start < max_wait_seconds:
        object_created: bool = await minio_check_if_object_exists(bucket_name, object_name)
        if object_created:
            return True
        await asyncio.sleep(0.1)
    return False


async def helper_wait_till_db_has_count_minio_objects(target_amount: int, max_wait_seconds: float = 5) -> bool:
    # Sleep till db has target amount of minio objects saved
    time_start = time.time()
    while time.time() - time_start < max_wait_seconds:
        count = await AudiobookChapter.count().where(AudiobookChapter.minio_object_name != None)  # noqa: E711
        if target_amount <= count:
            return True
        await asyncio.sleep(0.1)
    return False


# TODO Decide which testing method i want to use
# 1) use a test environment with real piccolo postgres client and minio client - will need to set up before and clear up after (or before)
# 2) use mock functions, what disadvantages does it have? uses string to find attributes? no external applications like db needed tho
# 3) are there other possibilities? read pytest docs?

# TODO Use https://github.com/litestar-org/pytest-databases#readme
# to fake databases and minio


@pytest.fixture(scope="function")
def test_client() -> Iterator[TestClient[Litestar]]:
    # Use this client only if the test does not access the test-database
    with TestClient(app=app, raise_server_exceptions=True) as client:
        yield client


@pytest.fixture(scope="function")
def test_client_db_reset() -> Iterator[TestClient[Litestar]]:
    # Use this client if the test accesses and modifies the test-database
    run_sync(create_db_tables(*TABLES, if_not_exists=True))
    try:
        with TestClient(app=app, raise_server_exceptions=True) as client:
            yield client
    finally:
        run_sync(drop_db_tables(*TABLES))


@pytest.fixture(scope="function")
def test_minio_client() -> Iterator[Minio]:
    minio_client = Minio(
        os.getenv("MINIO_URL"),
        os.getenv("MINIO_ACCESS_TOKEN"),
        os.getenv("MINIO_SECRET_KEY"),
        secure=False,
    )
    # Create bucket
    bucket = os.getenv("MINIO_AUDIOBOOK_BUCKET")
    with suppress(S3Error):
        minio_client.make_bucket(bucket)
    # Delete all objects in bucket
    objects = minio_client.list_objects(bucket)
    for obj in objects:
        minio_client.remove_object(bucket, obj.object_name)
    yield minio_client


def log_in_with_twitch(test_client: TestClient, httpx_mock: HTTPXMock) -> None:
    test_client.cookies[COOKIES["twitch"]] = "valid_access_token"
    httpx_mock.add_response(
        url="https://api.twitch.tv/helix/users",
        json={"data": [{"id": "123", "login": "abc", "display_name": "Abc", "email": "abc@example.com"}]},
    )


# TODO Add Logout function and test?

# TODO Login with github and google

# class BaseTest:
#     method_client: TestClient = None

#     def setup_method(self, _method):
#         BaseTest.method_client = TestClient(app)

#     def teardown_method(self, _method):
#         BaseTest.method_client = None

#     @classmethod
#     @contextlib.contextmanager
#     def method_client_context(cls):
#         client = TestClient(app)
#         try:
#             yield client
#         finally:
#             cls.example_client = None

#     @pytest.fixture(name="method_client_fixture")
#     def method_client_fixture(self) -> Generator[TestClient, None, None]:
#         with BaseTest.method_client_context() as client:
#             assert isinstance(client, TestClient)
#             yield client
