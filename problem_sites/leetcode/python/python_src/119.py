from typing import List

from math import factorial


class Solution:
    @staticmethod
    def ncr(n: int, k: int):
        return factorial(n) // (factorial(n - k) * factorial(k))

    def getRow(self, rowIndex: int) -> List[int]:
        return [self.ncr(rowIndex, k) for k in range(rowIndex + 1)]


# fmt: off
test_cases = [
    3,
    0,
    1,
    2,
    33,
]
results = [
    [1, 3, 3, 1],
    [1],
    [1, 1],
    [1, 2, 1],
    [1, 33, 528, 5456, 40920, 237336, 1107568, 4272048, 13884156, 38567100, 92561040, 193536720, 354817320, 573166440, 818809200, 1037158320, 1166803110, 1166803110, 1037158320, 818809200, 573166440, 354817320, 193536720, 92561040, 38567100, 13884156, 4272048, 1107568, 237336, 40920, 5456, 528, 33, 1],
]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.getRow(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
