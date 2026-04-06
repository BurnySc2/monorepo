"""
https://leetcode.com/problems/single-number/submissions/

"""


class Solution:
    def singleNumber(self, nums: list[int]) -> int:
        found = set()
        too_many = set()
        for i in nums:
            if i not in found and i not in too_many:
                found.add(i)
            elif i in found and i not in too_many:
                found.discard(i)
                too_many.add(i)
        return found.pop()
