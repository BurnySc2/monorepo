from typing import List
from collections import Counter


class Solution:
    def destCity(self, paths: List[List[str]]) -> str:
        start_counter = Counter()
        end_counter = Counter()
        for (u, v) in paths:
            start_counter[u] += 1
            end_counter[v] += 1
        for (v, count) in end_counter.items():
            if count == 1 and start_counter[v] == 0:
                return v
        return ""
