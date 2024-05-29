import time
from pathlib import Path

import aiohttp
import pytest

from examples.async_await.asyncio_download_upload import download_all_sites, download_file, download_site


@pytest.mark.asyncio
async def test_download_all_sites():
    urls = ["http://www.jython.org"] * 2
    results = await download_all_sites(urls)
    assert sum(result.content_length for result in results) > 0


@pytest.mark.xfail(reason="If download bandwidth is low, then this test may fail.")
@pytest.mark.asyncio
async def test_download_file():
    # With this download throttle, it should take at least 9 seconds to download the 1mb image at 100kb/s
    download_path = Path(__file__).parent / "my_file.zip"
    download_path_not_complete = Path(__file__).parent / "my_file_incomplete"

    # Cleanup from last time
    download_path.unlink(missing_ok=True)
    download_path_not_complete.unlink(missing_ok=True)

    # https://www.thinkbroadband.com/download
    file_url = "http://ipv4.download.thinkbroadband.com/5MB.zip"

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
    assert download_path.is_file()

    # Cleanup
    download_path.unlink()


@pytest.mark.asyncio
async def test_download_site():
    url = "http://www.jython.org"
    async with aiohttp.ClientSession() as session:
        res = await download_site(session, url)
    assert res.content_length > 0
