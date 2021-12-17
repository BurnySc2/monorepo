import os
from multiprocessing import Pool
from typing import List, Union

import deal


@deal.pre(lambda number: isinstance(number, int) or isinstance(number, float) and -10**15 < number < 10**15)
@deal.post(lambda result: isinstance(result, (int, float)))
@deal.ensure(lambda number, result: number != result)
@deal.has()
def do_math(number: Union[int, float]) -> Union[int, float]:
    return number + 3


@deal.pre(lambda number: isinstance(number, int) or isinstance(number, float) and -10**15 < number < 10**15)
@deal.post(lambda result: isinstance(result, (int, float)))
@deal.ensure(lambda number, result: number != result)
@deal.has()
async def do_math_async(number: Union[int, float]) -> Union[int, float]:
    return number + 3


@deal.pre(lambda number: 0 <= number < 10**6)
@deal.post(lambda result: isinstance(result, int))
@deal.ensure(lambda number, result: number <= result)
def cpu_bound_summing(number: int) -> int:
    return sum(i * i for i in range(number + 1))


def cpu_bound_summing_custom(number: int):
    """ Multiprocessing doesn't seem to like the library "deal". """
    return sum(i * i for i in range(number + 1))


@deal.pre(lambda numbers: 1 <= len(numbers) <= 10_000)
def find_sums(numbers: List[int]) -> List[int]:
    # Run on a minimum of 4 processes / CPU cores
    # If set to None or ommited, it will be automatically calculated based on the hardware
    at_least_4_processes = os.cpu_count() or 4
    at_least_4_processes = max(4, at_least_4_processes)
    with Pool(processes=at_least_4_processes) as pool:
        result = pool.map(cpu_bound_summing_custom, numbers)
        # The following returns an iterator of the result instead, for lazy evaluation:
        # result = pool.imap(cpu_bound_summing, numbers)
    return result


def do_multiprocessing() -> List[int]:
    numbers: List[int] = [50_000 + x for x in range(2_000)]
    return find_sums(numbers)
