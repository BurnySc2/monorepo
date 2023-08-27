from typing import List


class Solution:
    def removeElement(self, nums: List[int], val: int) -> int:
        if not nums:
            return 0

        index = 0
        while 1:
            if nums[index] == val:
                nums.pop(index)
            else:
                index += 1
            if index >= len(nums):
                return len(nums)
