"""
Given an integer n, return the number of trailing zeroes in n!.



https://leetcode.com/problems/factorial-trailing-zeroes/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter


class Solution:
    def trailingZeroes(self, n: int) -> int:
        # powers_of_five = [5 ** i for i in range(1, int(n ** (1 / 5)))]
        powers_of_five = (5 ** i for i in range(1, int(n ** (1 / 5)) + 2))
        return sum(n // factor for factor in powers_of_five)


test_cases = [30, 5, 3, 100]
results = [7, 1, 0, 24]
# test_cases = [1000000000000000000000]
# results = [249999999999999999997]
# test_cases = [10000]
# results = [2499]

import time


if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        t0 = time.perf_counter()
        my_solution = app.trailingZeroes(test_case)
        t1 = time.perf_counter()
        print(f"Team: {t1-t0}")
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
