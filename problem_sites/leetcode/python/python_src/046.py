"""
Given a collection of distinct integers, return all possible permutations.

https://leetcode.com/problems/permutations/
"""


from typing import List, Generator, Any


def permutation_generator(my_list: List[Any]) -> Generator[Any, None, None]:
    # Length of list: at least 1
    if len(my_list) == 1:
        yield my_list
        return
    for i, middle in enumerate(my_list):
        remaining_list = my_list[:i] + my_list[i + 1 :]
        for p in permutation_generator(remaining_list):
            yield [middle] + p


class Solution:
    def permute(self, nums: List[int]) -> List[List[int]]:
        return list(permutation_generator(nums))


test_cases = [[1, 2, 3]]
results = [[[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.permute(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
