"""
Given a string containing digits from 2-9 inclusive, return all possible letter combinations that the number could represent.

A mapping of digit to letters (just like on the telephone buttons) is given below. Note that 1 does not map to any letters.

https://leetcode.com/problems/letter-combinations-of-a-phone-number/
"""


from typing import Set, Tuple, List, Generator
from collections import Counter


class Solution:
    def letterCombinations(self, digits: str) -> List[str]:
        if not digits:
            return []

        digit_map = {
            "1": "",
            "2": "abc",
            "3": "def",
            "4": "ghi",
            "5": "jkl",
            "6": "mno",
            "7": "pqrs",
            "8": "tuv",
            "9": "wxyz",
            "0": "",
        }

        strings = [digit_map[digit] for digit in digits]

        def increment_at_index(my_list, index, strings):
            if index < 0:
                return False
            my_list[index] += 1
            if my_list[index] >= len(strings[index]):
                my_list[index] = 0
                increment_at_index(my_list, index - 1, strings)
            return True

        def my_generator(strings) -> Generator[List[int], None, None]:
            indices = [0 for _ in strings]
            limit = [len(string) - 1 for string in strings]
            yield indices
            while 1:
                result: bool = increment_at_index(indices, len(indices) - 1, strings)
                # Limit reached: break
                yield indices
                if indices == limit:
                    break
            return None

        combinations = []
        indices_generator = my_generator(strings)
        for indices in indices_generator:
            # print(indices)
            my_combination = "".join([string[index] for string, index in zip(strings, indices)])
            combinations.append(my_combination)

        # print(combinations)
        return combinations


test_cases = ["23"]
results = [["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.letterCombinations(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
