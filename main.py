import asyncio
import aiohttp
import multiprocessing


async def main():
    sites = ["http://www.jython.org", "http://olympus.realpython.org/dice"] * 80
    await download_all_sites(sites)
    await do_math(6)


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
        print(f"Response lengths: {response_lengths}")


async def do_math(number):
    return number + 3


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
    finally:
        loop.close()
