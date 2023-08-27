"""
https://leetcode.com/problems/find-peak-element/submissions/
"""

from typing import List


class Solution:
    def findPeakElement(self, nums: List[int]) -> int:
        return nums.index(max(nums))
