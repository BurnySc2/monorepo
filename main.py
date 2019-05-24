# Testing
from hypothesis import given
from hypothesis.strategies import text, integers, floats

# Coroutines and multiprocessing
import asyncio
import aiohttp
from multiprocessing import Process, Lock, Pool

# Type annotation / hints
from typing import List, Iterable, Union

# Other
import time, os, sys


async def main():
    sites: List[str] = ["http://www.jython.org", "http://olympus.realpython.org/dice"] * 80
    start_time = time.perf_counter()
    await download_all_sites(sites)
    end_time = time.perf_counter()
    print(f"Time for sites download taken: {end_time - start_time}")

    math_result = await do_math(6)

    start_time = time.perf_counter()
    do_multiprocessing()
    end_time = time.perf_counter()
    print(f"Time for multiprocessing taken: {end_time - start_time}")

    create_file()


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
            response_url = str(response.url)
            responses.append(response)

    return responses


async def do_math(number: Union[int, float]) -> Union[int, float]:
    return number + 3


def cpu_bound_summing(number: int) -> int:
    return sum(i * i for i in range(number))


def find_sums(numbers: Iterable[int]) -> List[int]:
    with Pool() as pool:
        result = pool.map(cpu_bound_summing, numbers)
    return result


def do_multiprocessing():
    numbers: List[int] = [5_000_000 + x for x in range(20)]
    sums: List[int] = find_sums(numbers)


def create_file():
    path = os.path.dirname(__file__)
    example_file = os.path.join(path, "hello_world.txt")
    with open(example_file, "w") as f:
        f.write("Hello world!\n")


if __name__ == "__main__":
    loop: asyncio.BaseEventLoop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

    # In Python 3.7 it is just::
    # asyncio.run(main())
