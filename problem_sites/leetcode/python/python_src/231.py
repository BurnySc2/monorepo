"""

https://leetcode.com/problems/power-of-two/
"""


class Solution:
    def isPowerOfTwo(self, n: int) -> bool:
        result = n
        remainder = 0
        while result > 1 and remainder == 0:
            result, remainder = divmod(result, 2)
        return bool(result == 1 and remainder == 0)
