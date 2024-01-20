"""
A program to start a task with at most n workers
"""

import time
from concurrent.futures import ThreadPoolExecutor
from threading import Semaphore

from loguru import logger

sema = Semaphore(2)


def task(number: int):
    # Limit amount of parallel tasks that can access a resource like db, file
    logger.info(f"Waiting for semaphore: {number}")
    with sema:
        logger.info(f"Entered semaphore: {number}")
        time.sleep(1)
    logger.info(f"Exiting semaphore: {number}")
    return number * number


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=3) as executor:
        numbers = [1, 2, 3, 4, 5]
        results = executor.map(
            task,
            numbers,
            # Allow at most 5 seconds per task, raises TimeoutError
            timeout=5,
        )
        for result in results:
            logger.info(result)
