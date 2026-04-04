"""
https://leetcode.com/problems/find-peak-element/submissions/
"""


class Solution:
    def findPeakElement(self, nums: list[int]) -> int:
        return nums.index(max(nums))
