from typing import Generator, List, Any, Dict


def permutation(my_list: List[Any]) -> List[Any]:
    # Length of list: at least 1
    if len(my_list) <= 1:
        return [my_list]
    result = []
    for i in range(len(my_list)):
        middle = my_list[i]
        remaining_list = my_list[:i] + my_list[i + 1 :]
        for p in permutation(remaining_list):
            result.append([middle] + p)
    return result


class Solution:
    def permuteUnique(self, nums: List[int]) -> List[List[int]]:
        return list({tuple(perm) for perm in permutation(nums)})
