import pytest
from litestar.status_codes import HTTP_200_OK
from litestar.testing import AsyncTestClient

from app import app


@pytest.mark.asyncio
async def test_index_test_route():
    async with AsyncTestClient(app=app) as client:
        response = await client.get("/test")
        assert response.status_code == HTTP_200_OK
        assert response.text == "Hello, world!"


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncTestClient(app=app) as client:
        response = await client.get("/health-check")
        assert response.status_code == HTTP_200_OK
        assert response.json() == {"hello": "world"}
