from bisect import bisect_left


class Solution:
    def searchInsert(self, nums: list[int], target: int) -> int:
        return bisect_left(nums, target)
