import os
import time
from pathlib import Path

import aiohttp
import pytest

from python_examples.examples.async_await.asyncio_download_upload import (
    download_all_sites,
    download_file,
    download_site,
)


@pytest.mark.asyncio
async def test_download_all_sites():
    urls = ['http://www.jython.org'] * 2
    results = await download_all_sites(urls)
    assert sum(result.content_length for result in results) > 0


@pytest.mark.asyncio
async def test_download_file():
    # With this download throttle, it should take at least 9 seconds to download the 1mb image at 100kb/s
    download_path = Path(__file__).parent / 'my_file.zip'
    download_path_not_complete = Path(__file__).parent / 'my_file_incomplete'

    # Cleanup from last time
    if os.path.isfile(download_path):
        os.remove(download_path)
    if os.path.isfile(download_path_not_complete):
        os.remove(download_path_not_complete)

    # https://www.thinkbroadband.com/download
    file_url = 'http://ipv4.download.thinkbroadband.com/5MB.zip'

    file_size = 5 * 2**20
    download_speed = 600 * 2**10
    estimated_download_time = file_size / download_speed
    assert estimated_download_time < 10
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
    assert estimated_download_time * 0.5 < t1 - t0 < estimated_download_time * 2
    assert os.path.isfile(download_path)

    # Cleanup
    os.remove(download_path)

    # Without throttle, it should take less than 3 seconds
    # t0 = time.perf_counter()
    # assert not os.path.isfile(download_path)
    # async with aiohttp.ClientSession() as session:
    #     result: bool = await download_file(
    #         session,
    #         url=file_url,
    #         file_path=download_path,
    #         temp_file_path=download_path_not_complete,
    #     )
    # t1 = time.perf_counter()
    # assert result
    # assert t1 - t0 < estimated_download_time * 0.8
    # assert os.path.isfile(download_path)

    # Cleanup
    # os.remove(download_path)


@pytest.mark.asyncio
async def test_download_site():
    url = 'http://www.jython.org'
    async with aiohttp.ClientSession() as session:
        res = await download_site(session, url)
    assert res.content_length > 0
