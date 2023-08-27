"""
Given an array of integers nums sorted in ascending order, find the starting and ending position of a given target value.

Your algorithm's runtime complexity must be in the order of O(log n).

If the target is not found in the array, return [-1, -1].

https://leetcode.com/problems/find-first-and-last-position-of-element-in-sorted-array/
"""
from typing import List


class Solution:
    def searchRange(self, nums: List[int], target: int) -> List[int]:
        start_index = -1
        end_index = -1
        for index, value in enumerate(nums):
            if target == value:
                if start_index == -1:
                    start_index = index
                end_index = index
            elif target < value:
                return [start_index, end_index]
        return [start_index, end_index]


test_cases = [[[1], -1], [[5, 7, 7, 8, 8, 10], 8], [[5, 7, 7, 8, 8, 10], 6]]
results = [[-1, -1], [3, 4], [-1, -1]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.searchRange(*test_case) == correct_result
        ), f"My result: {app.searchRange(*test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
