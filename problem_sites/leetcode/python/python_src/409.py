from collections import Counter


class Solution:
    def longestPalindrome(self, s: str) -> int:
        char_count = Counter(s)
        longest = 0
        for count in char_count.values():
            if longest % 2 == 0 or count % 2 == 0:
                longest += count
            else:
                longest += count - 1
        return longest


# fmt: off
test_cases = [
    "abccccdd",
    "bananas",
]
results = [
    7,
    5,
]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.longestPalindrome(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
