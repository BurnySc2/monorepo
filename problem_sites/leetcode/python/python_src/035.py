from typing import List


class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        for index, value in enumerate(nums):
            if value >= target:
                return index
        return len(nums)
