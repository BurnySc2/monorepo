"""
You are given an n x n 2D matrix representing an image.

Rotate the image by 90 degrees (clockwise).

Note:

You have to rotate the image in-place, which means you have to modify the input 2D matrix directly. DO NOT allocate another 2D matrix and do the rotation.

https://leetcode.com/problems/rotate-image/
"""

from typing import List


class Solution:
    def rotate(self, matrix: List[List[int]]) -> List[List[int]]:
        """
        Do not return anything, modify matrix in-place instead.
        Clockwise-rotation
        """
        height = len(matrix)
        width = len(matrix[0])

        indices = []
        for x in range(width - 1):
            for y in range(x, height - 1):
                if y + x >= height - 1:
                    continue
                indices.append((y, x))
        if height % 2 == 1:
            half_height = height // 2
            indices.append((half_height, half_height))

        print(indices)
        for y, x in indices:
            x1 = matrix[height - x - 1][y]
            x2 = matrix[height - y - 1][width - x - 1]
            x3 = matrix[x][width - y - 1]
            x4 = matrix[y][x]

            matrix[y][x] = x1
            matrix[height - x - 1][y] = x2
            matrix[height - y - 1][width - x - 1] = x3
            matrix[x][width - y - 1] = x4
        return matrix


# [
#   [ 5, 1, 9,11],
#   [ 2, 4, 8,10],
#   [13, 3, 6, 7],
#   [15,14,12,16]
# ],
# [
#   [15,13, 2, 5],
#   [14, 3, 4, 1],
#   [12, 6, 8, 9],
#   [16, 7,10,11]
# ]

# [
#   [1,2,3],
#   [4,5,6],
#   [7,8,9]
# ],
#   [7,4,1],
#   [8,5,2],
#   [9,6,3]

test_cases = [[[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]]
results = [[[7, 4, 1], [8, 5, 2], [9, 6, 3]], [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]]
# test_cases = [[[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]]]
# results = [[[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]]]
test_cases = [[[1, 2, 3, 4, 5], [6, 7, 8, 9, 10], [11, 12, 13, 14, 15], [16, 17, 18, 19, 20], [21, 22, 23, 24, 25]]]
results = [[[21, 16, 11, 6, 1], [22, 17, 12, 7, 2], [23, 18, 13, 8, 3], [24, 19, 14, 9, 4], [25, 20, 15, 10, 5]]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.rotate(test_case)
        assert repr(my_solution) == repr(
            correct_result
        ), f"My result: {app.rotate(test_case)}, correct result: {correct_result}"
