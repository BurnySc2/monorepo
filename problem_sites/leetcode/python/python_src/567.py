from typing import Generator, List, Any, Dict
from collections import Counter


class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        a = Counter(s1)
        b = Counter(s2)
        for char, count in a.items():
            if b[char] < count:
                return False
        return True
