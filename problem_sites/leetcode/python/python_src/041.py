"""
Given an unsorted integer array, find the smallest missing positive integer.

https://leetcode.com/problems/first-missing-positive/
"""
from typing import List
from heapq import heapify, heappop


class Solution:
    def firstMissingPositive(self, nums: List[int]) -> int:
        heapify(nums)
        next_number = 1
        while nums:
            popped_number = heappop(nums)
            # Because duplicates
            if popped_number < next_number:
                continue
            if next_number != popped_number:
                return next_number
            next_number += 1
        return next_number


test_cases = [[1, 2, 0], [3, 4, -1, 1], [7, 8, 9, 11, 12]]
results = [3, 2, 1]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.firstMissingPositive(test_case) == correct_result
        ), f"My result: {app.firstMissingPositive(test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
