import asyncio
from asyncio import Queue
import time

from aiohttp import ClientSession, TCPConnector
from loguru import logger

REQUEST_PER_SECOND = 20
WORKERS_AMOUNT = 6
WAIT_TIME = WORKERS_AMOUNT / REQUEST_PER_SECOND


async def create_tasks(queue: Queue):
    # https://jsonplaceholder.typicode.com/guide/
    logger.info("Creating tasks...")
    for i in range(1, 101):
        await queue.put(f"https://jsonplaceholder.typicode.com/posts/{i}")
    logger.info(f"Queue contains {queue.qsize()} items now")
    logger.info(f"Estimated seconds of workload: {queue.qsize() / REQUEST_PER_SECOND:.2f} seconds")


async def do_stuff(session: ClientSession, url: str, results: list):
    response = await session.get(url)
    if response.ok:
        response_json = await response.json()
        results.append(response_json)


async def worker(session: ClientSession, input_queue: Queue, results: list):
    while not input_queue.empty():
        t0 = time.perf_counter()
        url: str = await input_queue.get()
        # Get and store results
        await do_stuff(session, url, results)
        input_queue.task_done()
        t1 = time.perf_counter()
        # Respect rate limiting
        wait_time = WAIT_TIME + t0 - t1
        if wait_time > 0 and not input_queue.empty():
            await asyncio.sleep(wait_time)


async def main():
    queue = Queue()
    results = []
    await create_tasks(queue)
    logger.info("Starting workers...")
    async with ClientSession(
        connector=TCPConnector(
            # Limit amount of connections this ClientSession should posses
            limit=10,
            # Limit amount of connections per host
            limit_per_host=8,
        ),
        # How long each request can at most take - can be overridden in request individually
        timeout=10,
    ) as session:
        await asyncio.gather(*(asyncio.create_task(worker(
            session,
            queue,
            results,
        )) for _ in range(WORKERS_AMOUNT)))

    logger.info(f"Workers are done! Amount of results: {len(results)}")
    for result in results:
        logger.info(result)


def api_rate_limited_example():
    asyncio.run(main())


if __name__ == '__main__':
    api_rate_limited_example()
