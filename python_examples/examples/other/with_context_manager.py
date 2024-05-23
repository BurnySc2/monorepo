import time
from contextlib import contextmanager


class Timer:
    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.elapsed_time = time.time() - self.start_time
        print(f"Elapsed time: {self.elapsed_time:.4f} seconds")


@contextmanager
def timer():
    start_time = time.time()
    try:
        yield
    finally:
        elapsed_time = time.time() - start_time
        print(f"Elapsed time: {elapsed_time:.4f} seconds")


if __name__ == "__main__":
    with Timer() as timer:
        # Simulate a time-consuming operation
        sum = 0
        for i in range(1000000):
            sum += i
        print("Sum calculation complete")

    # Example use case:
    with timer():
        # Simulate a time-consuming operation
        sum = 0
        for i in range(1000000):
            sum += i
        print("Sum calculation complete")
