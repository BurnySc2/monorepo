"""
Given a non-negative integer numRows, generate the first numRows of Pascal's triangle.

https://leetcode.com/problems/pascals-triangle/
"""
from typing import List

# TO SLOW but the identical rust version works
class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        # O(n^2) solution
        biggest_area = 0
        previous_value = 0
        for index, start_height in enumerate(heights):
            if start_height == 0:
                continue
            # Filter out values where the next value is smaller than the previous
            if start_height <= previous_value:
                previous_value = start_height
                continue
            area = start_height
            for distance, end_height in enumerate(heights[index + 1 :], start=2):
                if end_height < start_height:
                    start_height = end_height
                area = max(area, start_height * distance)
            biggest_area = max(biggest_area, area)
        return biggest_area


if __name__ == "__main__":
    # fmt: off
    test_cases = [
        [2, 1, 5, 6, 2, 3],
    ]
    results = [
        10,
    ]
    # fmt: on

    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.largestRectangleArea(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
