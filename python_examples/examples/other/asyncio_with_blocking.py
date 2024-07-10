"""
This script shows how to run a task in a separate thread while in asyncio-context.
"""
import asyncio
import time

from loguru import logger


def blocking_task(number: int):
    if number == 5:
        raise TimeoutError()
    time.sleep(1)
    logger.info(number)
    return number * number


async def main():
    numbers = [1, 2, 3, 4, 5]

    for number in numbers:
        result = await asyncio.to_thread(blocking_task, number)
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
