# 202
# https://leetcode.com/problems/happy-number/

class Solution:
    def isHappy(self, n: int) -> bool:
        seen = {n}
        while 1:
            new_n = 0
            while n > 0:
                n, remainder = divmod(n, 10)
                new_n += remainder * remainder
            n = new_n
            if n == 1:
                return True
            if n in seen:
                return False
            seen.add(n)
