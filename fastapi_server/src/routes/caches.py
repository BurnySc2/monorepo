from asyncio.coroutines import iscoroutine
from collections.abc import Coroutine
from typing import Any

from litestar.stores.memory import MemoryStore

# MemoryStore https://docs.litestar.dev/2/usage/stores.html
global_cache = MemoryStore()


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
