"""
Given an array nums of n integers, are there elements a, b, c in nums such that a + b + c = 0? Find all unique triplets in the array which gives the sum of zero.


https://leetcode.com/problems/3sum/
"""

from typing import Set, Tuple, List
from collections import Counter


class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        if len(nums) < 3:
            return []
        counter: Counter = Counter(nums)
        sorted_list: List[int] = sorted(counter.keys())
        solutions: List[List[int]] = []
        for i, a in enumerate(sorted_list):
            if a > 0:
                break
            for b in sorted_list[i:]:
                if b == a and counter[b] < 2:
                    continue
                c: int = -a - b
                # To avoid duplicates
                if b > c:
                    continue
                if c in counter and (
                    # In the case of a==b+c where b==c, counter[b] > 1
                    c != b
                    or counter[b] > 1
                    # In the case of a==b==c==0
                    and (a != c or counter[a] > 2)
                ):
                    solutions.append([a, b, c])
        return solutions


test_cases = [[-1, -2, -3, 4, 1, 3, 0, 0, 0, 3, -2, 1, -2, 2, -1, 1, -5, 4, -3]]
results = [
    [
        [-5, 1, 4],
        [-5, 2, 3],
        [-3, -1, 4],
        [-3, 0, 3],
        [-3, 1, 2],
        [-2, -2, 4],
        [-2, -1, 3],
        [-2, 0, 2],
        [-2, 1, 1],
        [-1, -1, 2],
        [-1, 0, 1],
        [0, 0, 0],
    ]
]
# test_cases = [[-1, 0, 1, 2, -1, -4]]
# results = [[[-1, -1, 2], [-1, 0, 1]]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.threeSum(test_case)
        sorted_my_result = sorted([sorted(solution) for solution in my_result])
        sorted_correct_result = sorted([sorted(solution) for solution in correct_result])
        assert (
            sorted_my_result == sorted_correct_result
        ), f"My result ({len(sorted_my_result)}): {sorted_my_result}\n, correct result ({len(sorted_correct_result)}): {sorted_correct_result}"
