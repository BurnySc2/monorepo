class Solution:
    def removeElement(self, nums: list[int], val: int) -> int:
        if not nums:
            return 0

        index = 0
        while True:
            if nums[index] == val:
                nums.pop(index)
            else:
                index += 1
            if index >= len(nums):
                return len(nums)
