"""
Given a string containing just the characters '(', ')', '{', '}', '[' and ']', determine if the input string is valid.

https://leetcode.com/problems/valid-parentheses/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter


class Solution:
    def isValid(self, s: str) -> bool:
        stack = []
        pair = {
            "(": ")",
            "[": "]",
            "{": "}",
        }
        for i in s:
            if i in {"(", "[", "{"}:
                stack.append(i)
            elif stack and pair.get(stack[-1], None) == i:
                stack.pop()
            else:
                return False
        if not stack:
            return True
        return False
