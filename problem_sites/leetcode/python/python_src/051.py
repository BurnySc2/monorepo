"""
https://leetcode.com/problems/n-queens/
"""


class Solution:
    def solveNQueens(self, n: int) -> list[list[str]]:
        return []


# fmt: off
test_cases: list[int] = [4]
results: list[list[list[str]]] = [[]]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.solveNQueens(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
