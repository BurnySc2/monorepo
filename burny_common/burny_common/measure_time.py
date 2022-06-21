import time
from contextlib import contextmanager

from loguru import logger


@contextmanager
def time_this(label: str):
    start = time.perf_counter_ns()
    yield
    end = time.perf_counter_ns()
    logger.info(f'TIME {label}: {(end - start) / 1e9} sec')


# Use like this
if __name__ == '__main__':
    with time_this('square rooting'):
        for i in range(10**4):
            _x = i**0.5
