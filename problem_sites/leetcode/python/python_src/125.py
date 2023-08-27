"""
https://leetcode.com/problems/valid-palindrome/
"""


class Solution:
    def isPalindrome(self, s: str) -> bool:
        sanitized_string = "".join(i.lower() for i in s if i.isalnum())
        return sanitized_string == sanitized_string[::-1]
