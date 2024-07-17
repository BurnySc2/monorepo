"""
This script displays how to cancel the asyncio tasks if just one task fails.
"""

import asyncio

from loguru import logger

SEM = asyncio.Semaphore(4)


async def task(number: int):
    global SEM
    # Semaphore: Run at most 4 at a time
    async with SEM:
        if number == 4:
            raise TimeoutError()
        await asyncio.sleep(1)
        logger.info(number)
        return number * number


async def main():
    numbers = list(range(1, 100))
    tasks = [asyncio.create_task(task(number)) for number in numbers]

    done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    for future in done:
        exc = future.exception()
        if exc is not None:
            # Shuts down instantly on error
            raise exc
        result = await future
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
