import asyncio
import time
from contextlib import asynccontextmanager


class Timer:
    async def __aenter__(self):
        self.start_time = time.time()
        # return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_time = time.time() - self.start_time
        print(f"Elapsed time: {self.elapsed_time:.4f} seconds")


@asynccontextmanager
async def my_timer():
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_time = time.time() - start_time
        print(f"Elapsed time: {elapsed_time:.4f} seconds")


async def main():
    async with Timer() as _timer:
        # Simulate a time-consuming operation
        sum = 0
        for i in range(1000000):
            sum += i
        print("Sum calculation complete")

    # Example use case:
    async with my_timer():
        # Simulate a time-consuming operation
        sum = 0
        for i in range(1000000):
            sum += i
        print("Sum calculation complete")


if __name__ == "__main__":
    asyncio.run(main())
