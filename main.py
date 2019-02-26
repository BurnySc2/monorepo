# Testing
from dpcontracts import require, ensure
from hypothesis import given
from hypothesis.strategies import text, integers, floats

# Coroutines and multiprocessing
import asyncio
import aiohttp
from multiprocessing import Process, Lock, Pool

# Type annotation / hints
from typing import List, Iterable, Union

# Other
import time


async def main():
    sites: List[str] = [
        "http://www.jython.org",
        "http://olympus.realpython.org/dice",
    ] * 80
    await download_all_sites(sites)

    math_result = await do_math(6)

    start_time = time.perf_counter()
    do_multiprocessing()
    end_time = time.perf_counter()
    print(f"Time for multiprocessing taken: {end_time - start_time}")


@require(
    "First argument has to be a session object",
    lambda args: isinstance(args.session, aiohttp.ClientSession),
)
@require("Second argument has to be a url", lambda args: isinstance(args.url, str))
@require("Second argument can not be empty", lambda args: args.url != "")
@ensure(
    "Return value has to be a response",
    lambda args, result: isinstance(result, aiohttp.ClientResponse),
)
async def download_site(
    session: aiohttp.ClientSession, url: str
) -> aiohttp.ClientResponse:
    async with session.get(url) as response:
        return response


async def download_all_sites(sites: Iterable[str]) -> List[aiohttp.ClientResponse]:
    async with aiohttp.ClientSession() as session:
        tasks = [download_site(session, url) for url in sites]
        # Alternatively:
        # tasks = []
        # for url in sites:
        #     tasks.append(download_site(session, url))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # Or alternatively to the above:
        # responses = await asyncio.gather(
        #     *(download_site(session, url) for url in sites), return_exceptions=True
        # )
    return responses


@require(
    "Argument has to be a number", lambda args: isinstance(args.number, (int, float))
)
@ensure(
    "Return value needs to be a number",
    lambda args, result: isinstance(result, (int, float)),
)
async def do_math(number: Union[int, float]) -> Union[int, float]:
    return number + 3


@require("Argument has to be integer", lambda args: isinstance(args.number, int))
@ensure("Returnvalue has to be integer", lambda args, result: isinstance(result, int))
@ensure(
    "Returnvalue has to be zero or larger than zero", lambda args, result: result >= 0
)
def cpu_bound_summing(number: int) -> int:
    return sum(i * i for i in range(number))


@require("Argument has to be iterable", lambda args: iter(args.numbers))
@ensure(
    "Result needs to be same size as argument",
    lambda args, result: len(args) == len(result),
)
def find_sums(numbers: List[int]) -> List[int]:
    with Pool() as pool:
        result = pool.map(cpu_bound_summing, numbers)
    return result


def do_multiprocessing():
    numbers: List[int] = [5_000_000 + x for x in range(20)]
    sums: List[int] = find_sums(numbers)


if __name__ == "__main__":
    loop: asyncio.BaseEventLoop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
