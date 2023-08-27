from typing import List
from collections import Counter


class Solution:
    def findCenter(self, edges: List[List[int]]) -> int:
        my_counter = Counter()
        for (u, v) in edges:
            my_counter[u] += 1
            my_counter[v] += 1
            if my_counter[u] > 1:
                return u
            if my_counter[v] > 1:
                return v
        return -1
