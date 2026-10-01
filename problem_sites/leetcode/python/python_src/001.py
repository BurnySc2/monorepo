class Solution:
    def twoSum(self, nums: list[int], target: int) -> list[int]:
        my_dict = {}
        for index, value in enumerate(nums):
            val = target - value
            if val in my_dict:
                return [index, my_dict[val]]
            my_dict[value] = index
        return []


# fmt: off
test_cases: list[tuple[list[int], int]] = [([2, 7, 11, 15], 9)]
results: list[list[int]] = [[0, 1]]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.twoSum(*test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
