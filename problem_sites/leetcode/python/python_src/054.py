"""
Given a matrix of m x n elements (m rows, n columns), return all elements of the matrix in spiral order.

https://leetcode.com/problems/spiral-matrix/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter


class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        if not matrix:
            return []

        vectors = [[1, 0], [0, 1], [-1, 0], [0, -1]]
        vector_index = 0

        checked_indices: Set[Tuple[int, int]] = {(0, 0)}
        x, y = 0, 0
        output: List[int] = [matrix[0][0]]

        height, width = len(matrix), len(matrix[0])
        limit = height * width

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
            output.append(matrix[y][x])

            if len(output) == limit:
                return output
        return output


test_cases = [[[1, 2, 3], [4, 5, 6], [7, 8, 9]]]
results = [[1, 2, 3, 6, 9, 8, 7, 4, 5]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.spiralOrder(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
