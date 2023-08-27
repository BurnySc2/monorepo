"""
Given a non-negative integer numRows, generate the first numRows of Pascal's triangle.

https://leetcode.com/problems/pascals-triangle/
"""
from typing import List, Any, Generator
from math import factorial


def get_permutation_at_index(original: List[Any], index: int) -> List[Any]:
    """ Returns lexicographically ordered permutation at index 'index'.
    assert get_permutation_at_index(list("ABC"), 0) == list("ABC")
    assert get_permutation_at_index(list("ABC"), 5) == list("CBA")
    assert get_permutation_at_index(list("ABCD"), 23) == list("DCBA")
    """
    assert 0 <= index < factorial(len(original))
    if len(original) == 1:
        return original
    quotient, remainder = divmod(index, factorial(len(original) - 1))
    return [original[quotient]] + get_permutation_at_index(original[:quotient] + original[quotient + 1 :], remainder)


class Solution:
    def getPermutation(self, n: int, k: int) -> str:
        if n == 1:
            return "1"
        numbers = list(map(str, range(1, n + 1)))

        return "".join(get_permutation_at_index(numbers, k - 1))


# fmt: off
test_cases = [[3, 3], [4, 9], [1, 1], [3, 1], [8, 21092], [9, 233794], [9, 214267]]
results = ["213", "2314", "1", "123", "52378164", "683724591", "635749128"]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.getPermutation(*test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
