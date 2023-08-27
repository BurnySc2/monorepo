from typing import List, Tuple
import math


class Solution:
    def generate_number(self, string: str, length: int, difference: int) -> List[int]:
        if len(string) == length:
            return [int(string)]
        number = int(string[-1])
        numbers = []
        if number + difference < 10:
            numbers.extend(self.generate_number(string + str(number + difference), length, difference))
        if number - difference >= 0 and difference > 0:
            numbers.extend(self.generate_number(string + str(number - difference), length, difference))
        return numbers

    def numsSameConsecDiff(self, N: int, K: int) -> List[int]:
        if N == 1:
            return list(range(10))
        numbers = []
        for i in range(1, 10):
            new_numbers = self.generate_number(str(i), N, K)
            numbers.extend(new_numbers)
        return numbers


# fmt: off
test_cases = [
    [1, 0],
    [2, 0],
    [3, 7],
    [2, 1],
]
results = [
    [0,1,2,3,4,5,6,7,8,9],
    [11,22,33,44,55,66,77,88,99],
    [181, 292, 707, 818, 929],
    [10, 12, 21, 23, 32, 34, 43, 45, 54, 56, 65, 67, 76, 78, 87, 89, 98],
]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        test_case_copy = test_case.copy()
        my_result = app.numsSameConsecDiff(*test_case)
        my_result.sort()
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case_copy}"
