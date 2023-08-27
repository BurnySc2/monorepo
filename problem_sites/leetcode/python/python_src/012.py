"""
Roman numerals are represented by seven different symbols: I, V, X, L, C, D and M.

Symbol       Value
I             1
V             5
X             10
L             50
C             100
D             500
M             1000
For example, two is written as II in Roman numeral, just two one's added together. Twelve is written as, XII, which is simply X + II. The number twenty seven is written as XXVII, which is XX + V + II.

Roman numerals are usually written largest to smallest from left to right. However, the numeral for four is not IIII. Instead, the number four is written as IV. Because the one is before the five we subtract it making four. The same principle applies to the number nine, which is written as IX. There are six instances where subtraction is used:

I can be placed before V (5) and X (10) to make 4 and 9.
X can be placed before L (50) and C (100) to make 40 and 90.
C can be placed before D (500) and M (1000) to make 400 and 900.
Given an integer, convert it to a roman numeral. Input is guaranteed to be within the range from 1 to 3999.

https://leetcode.com/problems/integer-to-roman/
"""


class Solution:
    def intToRoman(self, num: int) -> str:
        """
        M = 1000
        D = 500
        C = 100
        L = 50
        X = 10
        V = 5
        I = 1
        """
        result_str = ""
        while num > 0:
            if num - 1000 >= 0:
                result_str += "M"
                num -= 1000
                continue
            elif num - 900 >= 0:
                result_str += "CM"
                num -= 900
                continue
            elif num - 500 >= 0:
                result_str += "D"
                num -= 500
                continue
            elif num - 400 >= 0:
                result_str += "CD"
                num -= 400
                continue
            elif num - 100 >= 0:
                result_str += "C"
                num -= 100
                continue
            elif num - 90 >= 0:
                result_str += "XC"
                num -= 90
                continue
            elif num - 50 >= 0:
                result_str += "L"
                num -= 50
                continue
            elif num - 40 >= 0:
                result_str += "XL"
                num -= 40
                continue
            elif num - 10 >= 0:
                result_str += "X"
                num -= 10
                continue
            elif num - 9 >= 0:
                result_str += "IX"
                num -= 9
                continue
            elif num - 5 >= 0:
                result_str += "V"
                num -= 5
                continue
            elif num - 4 >= 0:
                result_str += "IV"
                num -= 4
                continue
            elif num - 1 >= 0:
                result_str += "I"
                num -= 1
                continue

        return result_str


test_cases = [3, 4, 9, 58, 1994]
results = ["III", "IV", "IX", "LVIII", "MCMXCIV"]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.intToRoman(test_case) == correct_result
        ), f"My result: {app.intToRoman(test_case)}, correct result: {correct_result}"
