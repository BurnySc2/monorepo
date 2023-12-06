from heapq import heappop

from typing import List, DefaultDict
from collections import defaultdict

from string import ascii_uppercase

uppercases = set(ascii_uppercase)


class Solution:
    def detectCapitalUse(self, word: str) -> bool:
        return (
            # Word starts with capital letter
            word[0] in uppercases
            and not any(letter in uppercases for letter in word[1:])
            # All letters are capitals
            or all(letter in uppercases for letter in word)
            # All letters are lowercase
            or not any(letter in uppercases for letter in word)
        )
