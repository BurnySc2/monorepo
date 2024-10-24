import asyncio
import os
from asyncio.coroutines import iscoroutine
from collections.abc import AsyncGenerator, Coroutine
from contextlib import asynccontextmanager
from typing import Any

from litestar.stores.memory import MemoryStore

from prisma import Prisma

# MemoryStore https://docs.litestar.dev/2/usage/stores.html
global_cache = MemoryStore()

_db: Prisma | None = None
_lock = asyncio.Lock()


@asynccontextmanager
async def get_db() -> AsyncGenerator[Prisma, None]:
    # https://github.com/RobertCraigie/prisma-client-py/issues/103
    # TODO What if connection is interrupted?
    global _db
    if _db is None:
        async with _lock:
            if _db is None:
                db = Prisma()
                await db.connect()
                _db = db
    yield _db


# TODO Fix me, can't seem to keep the connection open (event loop closed)
if os.getenv("STAGE") == "test":

    @asynccontextmanager
    async def get_db() -> AsyncGenerator[Prisma, None]:
        async with Prisma() as db:
            yield db


async def cache_coroutine_result(
    key: str,
    coroutine: Coroutine[None, None, Any],
    expires_in: int | None = None,
    renew_for: int | None = None,
) -> Any:
    global global_cache
    assert iscoroutine(coroutine)
    result = await global_cache.get(key, renew_for=renew_for)
    if result is not None:
        coroutine.close()
        return result
    result = await coroutine
    await global_cache.set(key, result, expires_in=expires_in)
    return result
