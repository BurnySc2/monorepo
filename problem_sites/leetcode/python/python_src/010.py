"""
Given an input string (s) and a pattern (p), implement regular expression matching with support for '.' and '*'.

'.' Matches any single character.
'*' Matches zero or more of the preceding element.

The matching should cover the entire input string (not partial).

Note:

    s could be empty and contains only lowercase letters a-z.
    p could be empty and contains only lowercase letters a-z, and characters like . or *.


https://leetcode.com/problems/regular-expression-matching/
"""
from typing import List


class Solution:
    def sanitize_pattern(self, p: str):
        sanitized = []
        index = 0
        added = False
        while 1:
            if index >= len(p):
                break
            char = p[index]
            first = p[index : index + 2]
            second = p[index + 2 : index + 4]
            if len(second) == 2 and first[1] == "*" == second[1] and first[0] == second[0]:
                if not added:
                    sanitized.append(first[0])
                    sanitized.append(first[1])
                index += 2
                added = True
            else:
                sanitized.append(char)
                index += 1
                added = False
        return "".join(sanitized)

    def match_first_character(self, s: str, p: str):
        if s and p and (s[0] == p[0] or p[0] == "."):
            return True
        return False

    def isMatch(self, s: str, p: str) -> bool:
        p = self.sanitize_pattern(p)
        return self.isMatch2(s, p)

    def isMatch2(self, s: str, p: str) -> bool:
        # Detect end: match
        if not s and (not p or ("*" in p[:2] and len(p) == 2)):
            return True
        # Detect end: mismatch
        if not p:
            return False
        # Simple case: no asterisk
        if "*" not in p[:2]:
            if self.match_first_character(s, p):
                return self.isMatch2(s[1:], p[1:])
            else:
                return False
        # Asterisk case: Fork
        if "*" in p[:2]:
            if self.match_first_character(s, p):
                return any(
                    [
                        # Skip 1 character
                        self.isMatch2(s[1:], p),
                        # Skip asterisk pattern
                        self.isMatch2(s, p[2:]),
                    ]
                )
            else:
                # Skip asterisk pattern
                return self.isMatch2(s, p[2:])


test_cases = [
    ["aa", "a"],
    ["aa", "a*"],
    ["aab", "c*a*b"],
    ["mississippi", "mis*is*p*."],
    ["aaaaaaaaaaaaab", "a*a*a*a*a*a*a*a*a*a*a*a*b"],
    ["", "c*c*"],
]
results = [False, True, True, False, True, True]
# test_cases = [["mississippi", "mis*is*p*."]]
# results = [ False]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.isMatch(*test_case) == correct_result
        ), f"My result: {app.isMatch(*test_case)}, correct result: {correct_result}\nTest Case: {test_case}"
