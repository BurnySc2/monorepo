# 338. Counting Bits
# https://leetcode.com/problems/counting-bits/
from typing import List

class Solution:
    def countBits(self, n: int) -> List[int]:
        LIMIT = 10**5
        exponents = {2**i for i in range(1, 20) if 2**i <= LIMIT}
        ans = []
        last_exponent = 0
        for i in range(n+1):
            if i in exponents:
                # Case 2, 4, 8, 16, ...
                last_exponent = i
                ans.append(1)
            elif last_exponent == 0:
                # Case 0 and 1
                ans.append(i)
            else:
                ans.append(1 + ans[i - last_exponent])
        return ans
