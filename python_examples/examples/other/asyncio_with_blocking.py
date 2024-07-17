"""
This script shows how to run a task in a separate thread while in asyncio-context.
"""

import asyncio
import time
from threading import Semaphore

from loguru import logger

SEM = Semaphore(4)


def blocking_task(number: int):
    with SEM:
        if number == 4:
            raise TimeoutError()
        time.sleep(1)
        logger.info(number)
        return number * number


async def main():
    numbers = list(range(1, 100))

    tasks = [asyncio.create_task(asyncio.to_thread(blocking_task, number)) for number in numbers]
    done, _pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
    # TODO this only raises exception when done with all numbers
    for future in done:
        exc = future.exception()
        if exc is not None:
            for task in tasks:
                task.cancel()
            raise exc
        result = await future
        logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
