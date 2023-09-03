# 169
# https://leetcode.com/problems/majority-element/
from typing import List

class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        cache = {}
        for i in nums:
            count = cache.get(i, 0) + 1
            if count > len(nums) // 2:
                return i
            cache[i] = count