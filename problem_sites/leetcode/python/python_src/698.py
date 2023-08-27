from typing import List


class Solution:
    def rebuild_sum(self, lookup: List[int], target: int):
        assert lookup[target] > -1
        my_summands = []
        while target != 0:
            my_summands.append(lookup[target])
            target -= lookup[target]
        return my_summands

    def can_partition(self, nums: List[int], target: int):
        my_lookup = [-1 for _ in range(target + 1)]
        my_lookup[0] = 0
        nums.sort(reverse=True)
        for num in nums:
            for i in range(target, -1, -1):
                if my_lookup[i] > -1:
                    new_index = num + i
                    if new_index > target:
                        continue
                    if new_index < 0:
                        break
                    if my_lookup[new_index] == -1:
                        my_lookup[new_index] = num
                        if new_index == target:
                            # Reconstruct how the sum is set together
                            summands = self.rebuild_sum(my_lookup, target)
                            # sorted_nums = sorted(nums, reverse=True)
                            # sorted_summands = sorted(summands, reverse=True)
                            # print(f"Sorted nums: {sorted_nums}")
                            # print(f"Target: {target}")
                            # print(f"Sorted summands: {sorted_summands}")
                            # print()
                            return summands
        return []

    def canPartitionKSubsets(self, nums: List[int], k: int) -> bool:
        nums = nums.copy()
        nums_sum = sum(nums)
        if nums_sum % k == 1:
            return False
        target = nums_sum // k
        for i in range(k):
            sum_list = self.can_partition(nums, target)
            for j in sum_list:
                nums.remove(j)
        return not bool(nums)


# fmt: off
test_cases = [
    [
        [1, 1, 1, 1, 2, 2, 2, 2],
        4,
    ],
    [
        [4, 3, 2, 3, 5, 2, 1],
        4,
    ],
    [[1, 2, 3, 4], 3],
]

results = [
    True,
    True,
    False,
]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.canPartitionKSubsets(*test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
