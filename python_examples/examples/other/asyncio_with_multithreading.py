"""
This script shows how to create multiple threads to run in an executor while being able to limit how many will run.
"""

import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from loguru import logger


def my_function(number: int):
    if number == 4:
        raise TimeoutError()
    time.sleep(1)
    logger.info(number)
    return number * number


async def main():
    numbers = list(range(1, 100))

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [loop.run_in_executor(executor, my_function, number) for number in numbers]

        done, _pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_EXCEPTION)
        for future in done:
            exc = future.exception()
            if exc is not None:
                # Either one works and shuts down when the last currently running task ends
                # executor.shutdown(wait=False, cancel_futures=True)
                executor.shutdown(cancel_futures=True)
                raise exc
            result = await future
            logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
