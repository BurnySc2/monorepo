"""
Given an array of strings, group anagrams together.

https://leetcode.com/problems/group-anagrams/
"""


from typing import Set, Tuple, List, Generator, Dict
from collections import Counter


class MyCounter(Counter):
    def __repr__(self):
        return_list = []
        for key, value in sorted(self.items(), key=lambda item: item[0]):
            return_list.append(str(key) + str(value))
        return "".join(return_list)

    def __hash__(self):
        return hash(repr(self))


class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        anagrams: Dict[str, List[str]] = {}

        for anagram in strs:
            anagram_as_counter = MyCounter(anagram)
            repr_string = repr(anagram_as_counter)
            if repr_string not in anagrams:
                anagrams[repr_string] = [anagram]
            else:
                anagrams[repr_string].append(anagram)
        print(anagrams)
        return_list: List[str] = [value for value in anagrams.values()]
        return return_list


test_cases = [["eat", "tea", "tan", "ate", "nat", "bat"]]
results = [[["ate", "eat", "tea"], ["nat", "tan"], ["bat"]]]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.groupAnagrams(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
