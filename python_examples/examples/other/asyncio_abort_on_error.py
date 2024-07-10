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
        if number == 5:
            raise TimeoutError()
        await asyncio.sleep(1)
        logger.info(number)
        return number * number


async def main():
    numbers = [1, 2, 3, 4, 5]
    tasks = [asyncio.create_task(task(number)) for number in numbers]
    for future in asyncio.as_completed(tasks):
        result = await future
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
