"""
https://leetcode.com/problems/n-queens/
"""
from typing import List


class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        pass


# fmt: off
test_cases = ["0", " 0.1 ", "abc", "1 a", "2e10", " -90e3 ", "1e","e3", " 6e-1", "99e2.5", "53.5e93", "--6", "-+3", "95a54e53", ".0", "0.", ".-4", ".e1", "32.e-80123"]
results = [True, True, False, False, True, True, False, False, True, False, True, False, False, False, True, True, False, False, True]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.isNumber(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
