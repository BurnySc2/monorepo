"""
Given a positive integer n, generate a square matrix filled with elements from 1 to n2 in spiral order.

https://leetcode.com/problems/spiral-matrix-ii/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter


class Solution:
    def plusOne(self, digits: List[int]) -> List[int]:
        def increment_at_index(my_list: List[int], index: int):
            if index < 0:
                return False
            my_list[index] += 1
            if my_list[index] > 9:
                my_list[index] = 0
                return increment_at_index(my_list, index - 1)
            return True

        # Check if it was incremented, in the case of [9, 9] we need to insert "0" at index 0
        incremented: bool = increment_at_index(digits, index=len(digits) - 1)
        if not incremented:
            digits.insert(0, 1)

        return digits


test_cases = [[4, 3, 2, 1], [9, 9]]
results = [[4, 3, 2, 2], [1, 0, 0]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.plusOne(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
