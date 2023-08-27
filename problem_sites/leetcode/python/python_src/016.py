"""
Given a non-negative integer numRows, generate the first numRows of Pascal's triangle.

https://leetcode.com/problems/pascals-triangle/
"""
from typing import List

# TOO SLOW rust equivalent works though
import math


class Solution:
    def threeSumClosest(self, nums: List[int], target: int) -> int:
        closest = math.inf
        closest_value = None
        for index1, i1 in enumerate(nums):
            for index2, i2 in enumerate(nums[index1 + 1 :]):
                for index3, i3 in enumerate(nums[index1 + index2 + 2 :]):
                    value = i1 + i2 + i3
                    # print(f"{i1} {i2} {i3} = {value}")
                    result = abs(target - value)
                    if result < closest:
                        closest = result
                        closest_value = value
        return closest_value


if __name__ == "__main__":
    # fmt: off
    test_cases = [
        [[-1, 2, 1, -4], 1],
        [[0, 0, 0], 1]
    ]
    results = [
        2,
        0,
    ]
    # fmt: on

    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.threeSumClosest(*test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
