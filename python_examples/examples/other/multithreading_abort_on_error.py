"""
This script displays how to cancel the whole executor if just one thread errors.
"""

import time
from concurrent.futures import Future, ThreadPoolExecutor

from loguru import logger


def task(number: int):
    if number == 5:
        raise TimeoutError()
    time.sleep(1)
    logger.info(number)
    return number * number


if __name__ == "__main__":
    numbers = [1, 2, 3, 4, 5]
    with ThreadPoolExecutor() as executor:
        results = executor.map(
            task,
            numbers,
        )
        # Required if errors should be caught
        for result in results:
            pass

    with ThreadPoolExecutor() as executor:
        futures: list[Future] = [executor.submit(task, number) for number in numbers]
        # Required if errors should be caught
        for future in futures:
            future.result()
