from contextlib import contextmanager
from typing import Generator, List, Any

from loguru import logger
import time


def permutation(my_list: List[Any]) -> List[Any]:
    # Length of list: at least 1
    if len(my_list) == 1:
        yield my_list
        return
    result = []
    for i in range(len(my_list)):
        middle = my_list[i]
        remaining_list = my_list[:i] + my_list[i + 1 :]
        for p in permutation(remaining_list):
            result.append([middle] + p)
    return result


def permutation_generator(my_list: List[Any]) -> Generator[Any, None, None]:
    # Length of list: at least 1
    if len(my_list) == 1:
        yield my_list
        return
    for i, middle in enumerate(my_list):
        remaining_list = my_list[:i] + my_list[i + 1 :]
        for p in permutation_generator(remaining_list):
            yield [middle] + p


def permutation_backwards_generator(my_list: List[Any]) -> Generator[Any, None, None]:
    # Length of list: at least 1
    if len(my_list) == 1:
        yield my_list
        return
    for i in range(len(my_list) - 1, -1, -1):
        middle = my_list[i]
        remaining_list = my_list[:i] + my_list[i + 1 :]
        for p in permutation_backwards_generator(remaining_list):
            yield [middle] + p


if __name__ == "__main__":

    @contextmanager
    def time_this(label: str):
        start = time.perf_counter_ns()
        try:
            yield
        finally:
            end = time.perf_counter_ns()
            logger.info(f"TIME {label}: {(end-start)/1e9} sec")

    with time_this("Permutation"):
        for n in range(10 ** 4):
            data = list("123")
            for p in permutation_generator(data):
                pass
            for p in permutation_backwards_generator(data):
                pass

    data = list("123")
    for p in permutation_generator(data):
        print(p)

    print("###################")

    for p in permutation_backwards_generator(data):
        print(p)

    data = list("1234567")
    assert list(permutation_generator(data)) == list(permutation_backwards_generator(data))[::-1]
