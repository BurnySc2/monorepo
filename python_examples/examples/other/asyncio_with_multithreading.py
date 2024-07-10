"""
This script shows how to create multiple threads to run in an executor while being able to limit how many will run.
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

from loguru import logger


def task(number: int):
    if number == 5:
        raise TimeoutError()
    time.sleep(1)
    logger.info(number)
    return number * number


async def main():
    numbers = [1, 2, 3, 4, 5]

    loop = asyncio.get_running_loop()
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [loop.run_in_executor(executor, task, number) for number in numbers]
        for future in asyncio.as_completed(tasks):
            result = await future
            logger.info(result)


if __name__ == "__main__":
    asyncio.run(main())
