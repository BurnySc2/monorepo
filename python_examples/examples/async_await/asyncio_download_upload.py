import asyncio
import os
import time
from pathlib import Path
from typing import Iterable, List

import aiohttp
from loguru import logger


async def download_file(
    session: aiohttp.ClientSession,
    url: str,
    file_path: Path,
    temp_file_path: Path,
    download_speed: int = -1,
    chunk_size: int = 4096,
) -> bool:
    """
    Downloads an image (or a file even) from "url" and saves it to "temp_file_path". When the download is complete, it renames the file at "temp_file_path" to "file_path".
    It respects "download_speed" in bytes per second. If no parameter was given, it will ignore the download limit.

    Returns boolean if download was successful.
    """
    downloaded: float = 0
    # Download start time
    time_last_subtracted = time.perf_counter()
    # Affects sleep time and check size for download speed, should be between 0.1 and 1
    accuracy: float = 0.1

    # Check if file exists
    if not file_path.exists():
        try:
            async with session.get(url) as response:
                # Assume everything went well with the response, no connection or server errors
                assert response.status == 200
                # Open file in binary write mode
                os.makedirs(temp_file_path.parent, exist_ok=True)
                with temp_file_path.open('wb') as f:
                    # Download file in chunks
                    async for data in response.content.iter_chunked(chunk_size):
                        # Write data to file in asyncio-mode using aiofiles
                        f.write(data)
                        # Keep track of how much was downloaded
                        downloaded += chunk_size
                        # Wait if downloaded size has reached its download throttle limit
                        while download_speed > 0 and download_speed * accuracy < downloaded:
                            time_temp = time.perf_counter()
                            # This size should be the estimated downloaded size in the passed time
                            estimated_download_size = download_speed * (time_temp - time_last_subtracted)
                            downloaded -= estimated_download_size
                            time_last_subtracted = time_temp
                            await asyncio.sleep(accuracy)
            await asyncio.sleep(0.1)
            os.makedirs(file_path.parent, exist_ok=True)
            try:
                temp_file_path.rename(file_path)
                return True
            except PermissionError:
                # The file might be open by another process
                logger.info(f'Permissionerror: Unable to rename file from ({temp_file_path}) to ({file_path})')
        except asyncio.TimeoutError:
            # The server might suddenly not respond
            logger.info(f'Received timeout error in url ({url}) in file path ({file_path})!')
    else:
        # The file already exists
        logger.info(f'File for url ({url}) in file path ({file_path}) already exists!')
    return False


async def download_site(session: aiohttp.ClientSession, url: str) -> aiohttp.ClientResponse:
    async with session.get(url) as response:
        return response


async def download_all_sites(sites: Iterable[str]) -> List[aiohttp.ClientResponse]:
    async with aiohttp.ClientSession() as session:
        tasks = []
        for url in sites:
            # In python 3.7: asyncio.create_task instead of asyncio.ensure_future
            task = asyncio.ensure_future(download_site(session, url))
            tasks.append(task)

        # Run all tasks in "parallel" and wait until all of them are completed
        # responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Or to iterate over tasks as they complete (random order)
        responses = []
        for future in asyncio.as_completed(tasks):
            response = await future
            # response_url = str(response.url)
            responses.append(response)
    return responses


async def main():
    download_path = Path(__file__).parent / 'my_file.zip'
    download_path_not_complete = Path(__file__).parent / 'my_file_incomplete'
    file_url = 'http://ipv4.download.thinkbroadband.com/5MB.zip'

    download_speed = 1000 * 2**10
    async with aiohttp.ClientSession() as session:
        _result: bool = await download_file(
            session,
            url=file_url,
            file_path=download_path,
            temp_file_path=download_path_not_complete,
            download_speed=download_speed,
        )
    if download_path.exists():
        os.remove(download_path)
    if download_path_not_complete.exists():
        os.remove(download_path_not_complete)


if __name__ == '__main__':
    asyncio.run(main())
