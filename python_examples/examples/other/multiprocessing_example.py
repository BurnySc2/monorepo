from __future__ import annotations

import os
from multiprocessing import Pool


def do_math(number: float) -> float:
    return number + 3


async def do_math_async(number: float) -> float:
    return number + 3


def cpu_bound_summing(number: int) -> int:
    return sum(i * i for i in range(number + 1))


def find_sums(numbers: list[int]) -> list[int]:
    # Run on a minimum of 4 processes / CPU cores
    # If set to None or ommited, it will be automatically calculated based on the hardware
    at_least_4_processes = os.cpu_count() or 4
    at_least_4_processes = max(4, at_least_4_processes)
    with Pool(processes=at_least_4_processes) as pool:
        result = pool.map(cpu_bound_summing, numbers)
        # The following returns an iterator of the result instead, for lazy evaluation:
        # result = pool.imap(cpu_bound_summing, numbers)
    return result


def do_multiprocessing() -> list[int]:
    numbers: list[int] = [50_000 + x for x in range(2_000)]
    return find_sums(numbers)
