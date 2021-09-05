import os
from multiprocessing import Pool
from typing import Union, Iterable, List


async def do_math(number: Union[int, float]) -> Union[int, float]:
    return number + 3


def cpu_bound_summing(number: int) -> int:
    return sum(i * i for i in range(number))


def find_sums(numbers: Iterable[int]) -> List[int]:
    # Run on a minimum of 4 processes / CPU cores
    # If set to None or ommited, it will be automatically calculated based on the hardware
    at_least_4_processes = os.cpu_count() or 4
    at_least_4_processes = max(4, at_least_4_processes)
    with Pool(processes=at_least_4_processes) as pool:
        result = pool.map(cpu_bound_summing, numbers)
        # Returns an iterator of the result instead, for lazy evaluation:
        # result = pool.imap(cpu_bound_summing, numbers)
    return result


def do_multiprocessing() -> List[int]:
    numbers: List[int] = [50_000 + x for x in range(2_000)]
    return find_sums(numbers)
