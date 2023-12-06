from typing import List


class Solution:
    def minWindow(self, s: str, t: str) -> str:
        start_index = None
        end_index = None
        best_word: str = None
        test_set = set(t)
        current = set()
        for index, i in enumerate(s):
            if i in test_set:
                if i in current:
                    pass
        return best_word


test_cases = [["ADOBECODEBANC", "ABC"]]
results = ["BANC"]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.minWindow(*test_case) == correct_result
        ), f"My result: {app.minWindow(*test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
