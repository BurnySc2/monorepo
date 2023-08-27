"""
Given a m x n matrix, if an element is 0, set its entire row and column to 0. Do it in-place.

https://leetcode.com/problems/set-matrix-zeroes/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter


class Solution:
    def setZeroes(self, matrix: List[List[int]]) -> None:
        """
        Do not return anything, modify matrix in-place instead.
        """

        def set_zero(matrix, row, column, target_value):
            for y in range(0, len(matrix)):
                if matrix[y][column]:
                    matrix[y][column] = target_value
            for x in range(0, len(matrix[0])):
                if matrix[row][x]:
                    matrix[row][x] = target_value

        for y in range(0, len(matrix)):
            for x in range(0, len(matrix[0])):
                value = matrix[y][x]
                # Check if value is zero
                if value is not None and not value:
                    matrix[y][x] = None
                    set_zero(matrix, y, x, None)

        for y in range(0, len(matrix)):
            for x in range(0, len(matrix[0])):
                value = matrix[y][x]
                if value is None:
                    matrix[y][x] = 0

        return matrix


test_cases = [[[1, 1, 1], [1, 0, 1], [1, 1, 1]]]
results = [[[1, 0, 1], [0, 0, 0], [1, 0, 1]]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.setZeroes(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
