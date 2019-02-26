# The following results in errors "ValueError: attempted relative import beyond top-level package"
# from ..main import do_math, download_site
import sys

sys.path.append("..")
from main import do_math, download_site, download_all_sites
import pytest
import aiohttp
from hypothesis import given
import hypothesis.strategies as st

website_content_length = 19210


@pytest.mark.asyncio
async def test_download_site():
    async with aiohttp.ClientSession() as session:
        res = await download_site(session, "http://www.jython.org")
    assert website_content_length == res.content_length


@pytest.mark.asyncio
async def test_download_all_sites():
    urls = ["http://www.jython.org"] * 2
    results = await download_all_sites(urls)
    assert website_content_length * 2 == sum(
        result.content_length for result in results
    )


@pytest.mark.asyncio
async def test_do_math():
    res = await do_math(7)
    assert 10 == res


@pytest.mark.asyncio
@given(st.integers())
async def test_do_math_integers(value):
    assert 3 + value == await do_math(value)


@pytest.mark.asyncio
@given(st.floats(allow_infinity=False, allow_nan=False))
async def test_do_math_floats(value):
    assert 3 + value == await do_math(value)
