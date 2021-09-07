import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from main import do_math, download_all_sites, download_file
from examples.async_await.asyncio_download_upload import download_site
from examples.other.multiprocessing_example import cpu_bound_summing
import pytest
import aiohttp
import time
from pathlib import Path
from hypothesis import given
import hypothesis.strategies as st


@pytest.mark.asyncio
async def test_download_image():
    # With this download throttle, it should take at least 9 seconds to download the 1mb image at 100kb/s
    download_path = Path(__file__).parent / "my_file.zip"
    download_path_not_complete = Path(__file__).parent / "my_file_incomplete"

    # Cleanup from last time
    if os.path.isfile(download_path):
        os.remove(download_path)
    if os.path.isfile(download_path_not_complete):
        os.remove(download_path_not_complete)

    # https://www.thinkbroadband.com/download
    file_url = "http://ipv4.download.thinkbroadband.com/5MB.zip"

    file_size = 5 * 2**20
    download_speed = 1000 * 2**10
    estimated_download_time = file_size / download_speed
    assert estimated_download_time < 6
    t0 = time.perf_counter()
    async with aiohttp.ClientSession() as session:
        result: bool = await download_file(
            session,
            url=file_url,
            file_path=download_path,
            temp_file_path=download_path_not_complete,
            download_speed=download_speed,
        )
    t1 = time.perf_counter()
    assert result
    assert estimated_download_time * 0.8 < t1 - t0 < estimated_download_time * 1.2
    assert os.path.isfile(download_path)

    # Cleanup
    os.remove(download_path)

    # Without throttle, it should take less than 3 seconds
    t0 = time.perf_counter()
    assert not os.path.isfile(download_path)
    async with aiohttp.ClientSession() as session:
        result: bool = await download_file(
            session,
            url=file_url,
            file_path=download_path,
            temp_file_path=download_path_not_complete,
        )
    t1 = time.perf_counter()
    assert result
    assert t1 - t0 < estimated_download_time * 0.8
    assert os.path.isfile(download_path)

    # Cleanup
    os.remove(download_path)


@pytest.mark.asyncio
async def test_download_site():
    async with aiohttp.ClientSession() as session:
        res = await download_site(session, "http://www.jython.org")
    assert res.content_length > 0


@pytest.mark.asyncio
async def test_download_all_sites():
    urls = ["http://www.jython.org"] * 2
    results = await download_all_sites(urls)
    assert sum(result.content_length for result in results) > 0


@pytest.mark.asyncio
async def test_do_math():
    res = await do_math(7)
    assert res == 10


@pytest.mark.asyncio
@given(st.integers())
async def test_do_math_integers(value):
    assert 3 + value == await do_math(value)


@pytest.mark.asyncio
@given(st.floats(allow_infinity=False, allow_nan=False))
async def test_do_math_floats(value):
    assert 3 + value == await do_math(value)


@given(st.integers(min_value=0, max_value=10000))
def test_cpu_bound_summing(number):
    assert sum(i * i for i in range(number)) == cpu_bound_summing(number)


# TODO test which expects exception
