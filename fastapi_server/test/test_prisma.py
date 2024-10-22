import pytest
from litestar import Litestar
from litestar.status_codes import HTTP_200_OK
from litestar.testing import TestClient
from pytest_httpx import HTTPXMock

from prisma import Prisma
from prisma.cli import prisma
from test.base_test import test_client  # noqa: F401

_test_client = test_client


def setup_function(function):
    prisma.run(["migrate", "reset", "--force", "--skip-generate"], check=True)


@pytest.mark.asyncio
async def test_try_connect_with_prisma() -> None:
    async with Prisma() as db:
        results = await db.audiobookbook.find_many(where={})
        assert len(results) == 0
        await db.audiobookbook.create(
            data={
                "book_author": "test user",
                "book_title": "test",
                "uploaded_by": "test user",
                "chapter_count": 100,
            }
        )
        results = await db.audiobookbook.find_many(where={})
        assert len(results) == 1


@pytest.mark.asyncio
async def test_prisma_check_without_httpx_fixture(test_client: TestClient[Litestar]) -> None:
    async with Prisma() as db:
        results = await db.audiobookbook.find_many(where={})
        assert len(results) == 0
    response = test_client.get("/prisma-test")
    assert response.status_code == HTTP_200_OK
    assert response.text == "prisma success"
    async with Prisma() as db:
        results = await db.audiobookbook.find_many(where={})
        assert len(results) == 1


@pytest.mark.asyncio
@pytest.mark.httpx_mock(non_mocked_hosts=["localhost"])
async def test_prisma_check_with_httpx_fixture(test_client: TestClient[Litestar], httpx_mock: HTTPXMock) -> None:
    async with Prisma() as db:
        results = await db.audiobookbook.find_many(where={})
        assert len(results) == 0
    response = test_client.get("/prisma-test")
    assert response.status_code == HTTP_200_OK
    assert response.text == "prisma success"
    async with Prisma() as db:
        results = await db.audiobookbook.find_many(where={})
        assert len(results) == 1
