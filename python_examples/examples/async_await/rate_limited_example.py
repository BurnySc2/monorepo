import asyncio
import time
from typing import List, Tuple

from aiohttp import ClientSession, TCPConnector
from loguru import logger

REQUEST_PER_SECOND = 2000
WORKERS_AMOUNT = 20
MAX_RETRIES = 3
WAIT_TIME = WORKERS_AMOUNT / REQUEST_PER_SECOND
PRESERVE_ORDER = (i for i in range(10**1000))


async def create_tasks(queue: asyncio.PriorityQueue):
    # https://jsonplaceholder.typicode.com/guide/
    logger.info('Creating tasks...')
    for i in range(1, 101):
        # Priority queue is implemented with heap - need another integer to compare between elements
        # If elements have same priority, use the order in which they got created
        await queue.put((i, next(PRESERVE_ORDER), f'https://jsonplaceholder.typicode.com/posts/{i}', MAX_RETRIES))
    logger.info(f'Queue contains {queue.qsize()} items now')
    logger.info(f'Estimated seconds of workload: {queue.qsize() / REQUEST_PER_SECOND:.2f} seconds')


async def do_stuff(session: ClientSession, url: str, retry: int, results: list) -> bool:
    if retry <= 0:
        # Amount of retries exhausted
        return True
    try:
        response = await session.get(
            url,
            # How long each request can at most take
            timeout=0.005,
        )
        if response.ok:
            response_json = await response.json()
            results.append(response_json)
        return True
    except asyncio.TimeoutError:
        # Took too long to respond
        return False


async def worker(session: ClientSession, input_queue: asyncio.PriorityQueue, results: list):
    while not input_queue.empty():
        t0 = time.perf_counter()
        item: Tuple[int, int, str, int] = await input_queue.get()
        _priority, _, url, retry = item
        # Get and store results
        success = await do_stuff(session, url, retry, results)
        if not success:
            # Retry later
            await input_queue.put((_priority, next(PRESERVE_ORDER), url, retry - 1))
        input_queue.task_done()
        t1 = time.perf_counter()
        # Respect rate limiting
        wait_time = WAIT_TIME + t0 - t1
        if wait_time > 0 and not input_queue.empty():
            await asyncio.sleep(wait_time)


async def request_concurrently() -> float:
    t0 = time.perf_counter()
    queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
    results: List[dict] = []
    await create_tasks(queue)
    logger.info('Starting workers...')
    async with ClientSession(
        connector=TCPConnector(
            # Limit amount of connections this ClientSession should posses
            limit=40,
            # Limit amount of connections per host
            limit_per_host=20,
        ),
    ) as session:
        tasks = []
        for _ in range(WORKERS_AMOUNT):
            tasks.append(
                asyncio.create_task(
                    worker(
                        session,
                        queue,
                        results,
                    ),
                ),
            )
        await asyncio.gather(*tasks)

    t1 = time.perf_counter()
    logger.info(f'Workers are done! Amount of results: {len(results)}')
    return t1 - t0


async def request_sequentially() -> float:
    logger.info('Starting sequentially...')
    t0 = time.perf_counter()
    async with ClientSession() as session:
        for i in range(1, 101):
            result = await session.get(f'https://jsonplaceholder.typicode.com/posts/{i}')
            if result.ok:
                await result.json()
    t1 = time.perf_counter()
    logger.info('Sequentially done!')
    return t1 - t0


async def api_rate_limited_example():
    t_sequentially = await request_sequentially()
    t_concurrently = await request_concurrently()
    logger.info(t_sequentially)
    logger.info(t_concurrently)
    assert t_concurrently <= t_sequentially, f'{t_concurrently} <= {t_sequentially}'


def main():
    asyncio.run(api_rate_limited_example())


if __name__ == '__main__':
    main()
