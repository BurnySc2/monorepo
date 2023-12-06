"""
https://leetcode.com/problems/single-number-ii/

"""
from typing import List


class Solution:
    def singleNumber(self, nums: List[int]) -> int:
        found = set()
        too_many = set()
        for i in nums:
            if i not in found and i not in too_many:
                found.add(i)
            elif i in found and i not in too_many:
                found.discard(i)
                too_many.add(i)
        return found.pop()
