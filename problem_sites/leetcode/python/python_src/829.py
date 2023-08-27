"""
Given a positive integer N, how many ways can we write it as a sum of consecutive positive integers?

https://leetcode.com/problems/consecutive-numbers-sum/
"""


from typing import Set, Tuple, List, Generator, Dict


class Solution:
    def get_triangle_numbers(self) -> Generator[Tuple[int, int], None, None]:
        """ Endless generator for triangle numbers: [(1, 1), (2, 3), (3, 6), (4, 10) ... """
        i = 1
        n = 1
        while 1:
            yield (i, n)
            i += 1
            n += i

    def consecutiveNumbersSum(self, N: int) -> int:
        sums = 0
        for i, n in self.get_triangle_numbers():
            if n > N:
                break
            if (N - n) % i == 0:
                sums += 1
        return sums


""" Use triangle numbers to find out how many sums there are
for i in range(1, 10):
    print(f"{2*i+1} = {i} + {i+1}")
print()
for i in range(1, 10):
    print(f"{3*i+3} = {i} + {i+1} + {i+2}")
print()
for i in range(1, 10):
    print(f"{4*i+6} = {i} + {i+1} + {i+2} + {i+3}")
print()
for i in range(1, 10):
    print(f"{5*i+10} = {i} + {i+1} + {i+2} + {i+3} + {i+4}")


3 = 1 + 2
5 = 2 + 3
7 = 3 + 4
9 = 4 + 5
11 = 5 + 6
13 = 6 + 7
15 = 7 + 8
17 = 8 + 9
19 = 9 + 10

6 = 1 + 2 + 3
9 = 2 + 3 + 4
12 = 3 + 4 + 5
15 = 4 + 5 + 6
18 = 5 + 6 + 7
21 = 6 + 7 + 8
24 = 7 + 8 + 9
27 = 8 + 9 + 10
30 = 9 + 10 + 11

10 = 1 + 2 + 3 + 4
14 = 2 + 3 + 4 + 5
18 = 3 + 4 + 5 + 6
22 = 4 + 5 + 6 + 7
26 = 5 + 6 + 7 + 8
30 = 6 + 7 + 8 + 9
34 = 7 + 8 + 9 + 10
38 = 8 + 9 + 10 + 11
42 = 9 + 10 + 11 + 12

15 = 1 + 2 + 3 + 4 + 5
20 = 2 + 3 + 4 + 5 + 6
25 = 3 + 4 + 5 + 6 + 7
30 = 4 + 5 + 6 + 7 + 8
35 = 5 + 6 + 7 + 8 + 9
40 = 6 + 7 + 8 + 9 + 10
45 = 7 + 8 + 9 + 10 + 11
50 = 8 + 9 + 10 + 11 + 12
55 = 9 + 10 + 11 + 12 + 13
"""

"""
Example 1:

Input: 5
Output: 2
Explanation: 5 = 5 = 2 + 3
Example 2:

Input: 9
Output: 3
Explanation: 9 = 9 = 4 + 5 = 2 + 3 + 4
Example 3:

Input: 15
Output: 4
Explanation: 15 = 15 = 8 + 7 = 4 + 5 + 6 = 1 + 2 + 3 + 4 + 5
"""

test_cases = [15]
results = [4]  # 15 = 15 = 8 + 7 = 4 + 5 + 6 = 1 + 2 + 3 + 4 + 5

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.consecutiveNumbersSum(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
