from typing import List


class Solution:
    def lengthOfLongestSubstring(self, s: str) -> int:
        if not s:
            return 0
        my_dict = {}
        longest = 0
        start = 0
        for index, char in enumerate(s):
            if char in my_dict:
                j = my_dict[char]
                if j >= start:
                    longest = max(longest, index - start)
                    start = j + 1
            my_dict[char] = index
        return max(longest, len(s) - start)


# fmt: off
test_cases = [
    "abcabcbb",
    "bbbbb",
    "pwwkew",
    " ",
    "",
    "au",
    "cdd",
    "dvdf",
    "abba",
]
results = [
    3, 1, 3, 1, 0, 2, 2, 3, 2
]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.lengthOfLongestSubstring(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
