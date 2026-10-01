from collections import Counter


class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        a = Counter(s1)
        b = Counter(s2)
        return all(b[char] >= count for char, count in a.items())
