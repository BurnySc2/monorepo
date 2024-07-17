"""
This script displays how to cancel the whole executor if just one thread errors.
"""

import time
from concurrent.futures import FIRST_EXCEPTION, Future, ThreadPoolExecutor, wait

from loguru import logger


def task(number: int):
    if number == 4:
        raise TimeoutError()
    time.sleep(1)
    logger.info(number)
    return number * number


if __name__ == "__main__":
    numbers = list(range(1, 100))
    # with ThreadPoolExecutor(max_workers=4) as executor:
    #     results = executor.map(
    #         task,
    #         numbers,
    #     )
    #     # Required if errors should be caught. Shuts down after current running task ends
    #     for result in results:
    #         pass

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures: list[Future] = [executor.submit(task, number) for number in numbers]
        # Required if errors should be caught
        results = wait(futures, return_when=FIRST_EXCEPTION)
        done, not_done = results.done, results.not_done
        for future in done:
            exc = future.exception()
            if exc is not None:
                # Either one works and shuts down when the last currently running task ends
                # executor.shutdown(wait=False, cancel_futures=True)
                executor.shutdown(cancel_futures=True)
                raise exc
