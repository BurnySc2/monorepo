from typing import List, Any


def get_next_permutation(perm: List[Any]):
    for i in reversed(range(len(perm) - 1)):
        last = perm[i]
        for j in reversed(range(i + 1, len(perm))):
            prev = perm[j]
            if prev > last:
                perm[i], perm[j] = perm[j], perm[i]
                perm[i + 1 :] = sorted(perm[i + 1 :])
                return perm
    perm.sort()
    return perm


class Solution:
    def nextPermutation(self, nums: List[int]) -> None:
        get_next_permutation(nums)
