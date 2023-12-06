from typing import List


class Solution:
    def merge(self, intervals: List[List[int]]) -> List[List[int]]:
        if len(intervals) < 2:
            return intervals
        intervals.sort()
        start, end = None, None
        results = []
        for interval in intervals:
            if start is None:
                start, end = interval
                continue
            c_start, c_end = interval
            if start <= c_start and c_end <= end:
                continue
            if c_start <= end:
                end = c_end
            else:
                results.append([start, end])
                start, end = c_start, c_end
        results.append([start, end])
        return results


test_cases = [[[1, 3], [2, 6], [8, 10], [15, 18]], [[1, 4], [4, 5]], [[1, 4], [0, 4]], [[1, 4], [2, 3]]]
results = [[[1, 6], [8, 10], [15, 18]], [[1, 5]], [[0, 4]], [[1, 4]]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.merge(test_case) == correct_result
        ), f"My result: {app.merge(test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
