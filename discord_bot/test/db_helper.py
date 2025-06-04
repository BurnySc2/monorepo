from typing import Any, Iterator
import pytest
import pytest_asyncio
from models import DiscordMessage
from piccolo_conf_test import db_path


from contextlib import asynccontextmanager


@asynccontextmanager
async def db_manager():
    await DiscordMessage.create_table(if_not_exists=True)
    try:
        yield None
    finally:
        db_path.unlink(missing_ok=True)


@pytest_asyncio.fixture(scope="function")
async def empty_database():
    async with db_manager() as db:
        yield db
