"""
26. Remove Duplicates from Sorted Array

https://leetcode.com/problems/remove-duplicates-from-sorted-array/
"""


class Solution:
    def removeDuplicates(self, nums: list[int]) -> int:
        if not nums:
            return 0
        index = 0
        amount_in_list = len(nums)
        while True:
            if index + 1 > len(nums) - 1:
                break
            if nums[index] == nums[index + 1]:
                nums.pop(index)
                amount_in_list -= 1
            else:
                index += 1
        return amount_in_list
