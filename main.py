# Testing
from dpcontracts import require, ensure
from hypothesis import given
from hypothesis.strategies import text, integers, floats

# Coroutines and multiprocessing
import asyncio
import aiohttp
from multiprocessing import Process, Lock, Pool


async def main():
    sites = ["http://www.jython.org", "http://olympus.realpython.org/dice"] * 80
    await download_all_sites(sites)
    await do_math(6)


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
async def download_site(session, url):
    async with session.get(url) as response:
        return response


async def download_all_sites(sites):
    async with aiohttp.ClientSession() as session:
        tasks = [download_site(session, url) for url in sites]
        # tasks = []
        # for url in sites:
        #     tasks.append(download_site(session, url))
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        response_lengths = [response.content_length for response in responses]
        # print(f"Response lengths: {response_lengths}")
    return responses


@require(
    "Argument has to be a number", lambda args: isinstance(args.number, (int, float))
)
@ensure(
    "Return value needs to be a number",
    lambda args, result: isinstance(result, (int, float)),
)
async def do_math(number):
    return number + 3


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
