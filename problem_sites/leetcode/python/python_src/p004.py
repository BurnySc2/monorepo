from typing import List


class Solution:
    def findMedianSortedArrays(self, nums1: List[int], nums2: List[int]) -> float:
        merged = sorted(nums1 + nums2)
        count = len(merged)
        if count % 2 == 1:
            return merged[count // 2]
        else:
            index = (count // 2) - 1
            return sum(merged[index : index + 2]) / 2
