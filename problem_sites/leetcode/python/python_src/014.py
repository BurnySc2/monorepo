"""
Write a function to find the longest common prefix string amongst an array of strings.

If there is no common prefix, return an empty string "".

https://leetcode.com/problems/longest-common-prefix/
"""

from typing import List


class Solution:
    def longestCommonPrefix(self, strs: List[str]) -> str:
        prefix = ""
        if not strs:
            return ""

        # Smallest word
        smallest = len(min(strs, key=lambda u: len(u)))
        end_found = False

        for index in range(smallest):
            current_char = ""
            for word in strs:
                if current_char == "":
                    current_char = word[index]
                elif word[index] == current_char:
                    pass
                else:
                    end_found = True
                    break

            if end_found:
                break

            prefix += current_char

        return prefix


test_cases = [["flower", "flow", "flight"], ["dog", "racecar", "car"]]
results = ["fl", ""]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.longestCommonPrefix(test_case) == correct_result
        ), f"My result: {app.longestCommonPrefix(test_case)}, correct result: {correct_result}"
