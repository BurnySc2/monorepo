"""
https://leetcode.com/problems/reverse-words-in-a-string/

"""


class Solution:
    def reverseWords(self, s: str) -> str:
        s = s.strip()
        while "  " in s:
            s = s.replace("  ", " ")
        return " ".join(s.split(" ")[::-1])
