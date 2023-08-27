from typing import Generator, List, Any, Dict


def get_previous_permutation(perm: List[Any]):
    if len(perm) <= 1:
        return perm
    for i in reversed(range(len(perm) - 1)):
        last = perm[i]
        for j in reversed(range(i + 1, len(perm))):
            prev = perm[j]
            if prev < last:
                perm[i], perm[j] = perm[j], perm[i]
                return perm
    return perm


class Solution:
    def prevPermOpt1(self, A: List[int]) -> List[int]:
        return get_previous_permutation(A)


assert Solution().prevPermOpt1([4, 3, 2, 1]) == [3, 4, 2, 1], Solution().prevPermOpt1([4, 3, 2, 1])
assert Solution().prevPermOpt1([3, 1, 1, 3]) == [1, 3, 1, 3], Solution().prevPermOpt1([3, 1, 1, 3])
