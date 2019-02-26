# The following results in errors "ValueError: attempted relative import beyond top-level package"
# from ..main import do_math, download_site
import sys

sys.path.append("..")
from main import do_math, download_site, download_all_sites
import pytest
import aiohttp


@pytest.mark.asyncio
async def test_download_site():
    async with aiohttp.ClientSession() as session:
        res = await download_site(session, "http://www.jython.org")
    assert 19210 == res.content_length


@pytest.mark.asyncio
async def test_do_math():
    res = await do_math(7)
    assert 10 == res
