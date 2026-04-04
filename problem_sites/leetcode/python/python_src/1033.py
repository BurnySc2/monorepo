class Solution:
    def numMovesStones(self, a: int, b: int, c: int) -> list[int]:
        a, b, c = sorted([a, b, c])
        max_moves = c - a - 2
        min_moves = 2
        if c - a == 2 and c - b == 1:
            min_moves = 0
        elif c - b <= 2 or b - a <= 2:
            min_moves = 1
        return min_moves, max_moves
