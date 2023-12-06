"""
Given a matrix of m x n elements (m rows, n columns), return all elements of the matrix in spiral order.

https://leetcode.com/problems/spiral-matrix/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter

a = ""
a.isalnum()


class Solution:
    def countAndSay(self, n: int) -> str:
        string = "1"
        if n == 1:
            return string

        def get_next_string(my_string: str) -> str:
            value = None
            count = 0
            return_string = []
            for i in my_string:
                if value is None:
                    value = i
                    count = 1
                elif value != i:
                    return_string.extend([str(count), str(value)])
                    value = i
                    count = 1
                elif value == i:
                    count += 1
            return_string.extend([str(count), str(value)])
            return "".join(return_string)

        i = 1
        while i < n:
            string = get_next_string(string)
            i += 1
        return string


test_cases = [1, 2, 3, 4]
results = ["1", "11", "21", "1211"]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.countAndSay(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
