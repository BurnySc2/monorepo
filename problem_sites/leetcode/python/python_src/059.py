"""
Given a positive integer n, generate a square matrix filled with elements from 1 to n2 in spiral order.

https://leetcode.com/problems/spiral-matrix-ii/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter


class Solution:
    def generateMatrix(self, n: int) -> List[List[int]]:
        if not n:
            return [[]]

        matrix = [[-1 for x in range(n)] for y in range(n)]

        vectors = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        vector_index = 0

        checked_indices: Set[Tuple[int, int]] = {(0, 0)}
        x, y = 0, 0
        output: List[int] = [matrix[0][0]]

        height, width = len(matrix), len(matrix[0])
        limit = height * width

        matrix[y][x] = 1
        counter = 1

        while height > 1 or width > 1:
            delta_x, delta_y = vectors[vector_index]
            new_x = x + delta_x
            new_y = y + delta_y
            if (new_x, new_y) in checked_indices or not (0 <= new_x < width) or not (0 <= new_y < height):
                vector_index += 1
                vector_index %= len(vectors)
                delta_x, delta_y = vectors[vector_index]
                new_x = x + delta_x
                new_y = y + delta_y

            x, y = new_x, new_y
            checked_indices.add((x, y))
            # print(f"Added {(x, y)} with value {matrix[y][x]}")
            counter += 1
            matrix[y][x] = counter

            if len(checked_indices) == limit:
                return matrix
        return matrix


test_cases = [3]
results = [[[1, 2, 3], [8, 9, 4], [7, 6, 5]]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.generateMatrix(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
