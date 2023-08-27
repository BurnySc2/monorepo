# class Solution:
#     def twoSum(self, nums: List[int], target: int) -> List[int]:
#         for i, a in enumerate(nums):
#             index_offset = i + 1
#             for j, b in enumerate(nums[index_offset:]):
#                 if a + b == target:
#                     return [i, index_offset+j]

from typing import List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        my_set = set(nums)
        for i, value1 in enumerate(nums):
            index_offset = i + 1
            if (target - value1) not in my_set:
                continue
            for j, value2 in enumerate(nums[index_offset:]):
                if value1 + value2 == target:
                    return [i, index_offset + j]


# num = [2,7,11,15]
# target = 9
#
# class Solution:
#     def twoSum(self, num, target):
#         for i in range(len(num)):
#             check = target - num[i]
#             j = i
#             for k in range(len(num) - j):
#                 if check == num[k]:
#                     return(i, k)
#
# solver = Solution()
# result = solver.twoSum(num, target)
# print(result)
