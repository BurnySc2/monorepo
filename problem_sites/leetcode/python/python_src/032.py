"""
Given a string containing just the characters '(' and ')', find the length of the longest valid (well-formed) parentheses substring.

https://leetcode.com/problems/longest-valid-parentheses/
"""


class Solution:
    def validParentheses(self, s: str) -> bool:
        open_parentheses = 0
        for i in s:
            if i == "(":
                open_parentheses += 1
            elif open_parentheses <= 0:
                return False
            else:
                open_parentheses -= 1
        if open_parentheses > 0:
            return False
        return True

    def longestValidParentheses(self, s: str) -> int:
        # TODO Too slow but should work
        """
        Cases:
            - More closed brackets than open brackets encountered
            - No valid pairs at first (lots of open brackets in a row)
        """
        results = []
        length = len(s)
        for start_index in range(0, length, 1):
            if s[start_index] == ")":
                continue
            offset = length - start_index
            start_range = offset + offset % 2
            min_window_size = max(results, default=2)
            for offset_index in range(start_range, min_window_size - 1, -2):
                end_index = start_index + offset_index
                if end_index - start_index < min_window_size:
                    break
                substring = s[start_index:end_index]
                if self.validParentheses(substring):
                    results.append(len(substring))
        return max(results, default=0)


test_cases = ["(()", ")()())", "())()()()", "())((())()", "())((()))", "()(()", "))(()))()"]
results = [2, 4, 6, 6, 6, 2, 4]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.longestValidParentheses(test_case) == correct_result
        ), f"My result: {app.longestValidParentheses(test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
