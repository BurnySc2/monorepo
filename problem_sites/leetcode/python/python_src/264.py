from heapq import heappush, heappop, heapify


class Solution:
    def __init__(self):
        self.ugly_numbers_set = set()
        self.generate_ugly_numbers(1690)
        self.ugly_numbers = sorted(self.ugly_numbers_set)

    def generate_ugly_numbers(self, limit_amount: int):
        heap = [1]
        while len(self.ugly_numbers_set) < limit_amount:
            value = heappop(heap)
            if value in self.ugly_numbers_set:
                continue
            self.ugly_numbers_set.add(value)
            heappush(heap, value * 2)
            heappush(heap, value * 3)
            heappush(heap, value * 5)

    def nthUglyNumber(self, n: int) -> int:
        return self.ugly_numbers[n - 1]


if __name__ == "__main__":
    # fmt: off
    test_cases = [
        1,
        10,
    ]
    results = [
        1,
        12,
    ]
    # fmt: on

    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        test_case_copy = test_case.copy() if hasattr(test_case, "copy") else test_case
        my_result = app.nthUglyNumber(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case_copy}"
