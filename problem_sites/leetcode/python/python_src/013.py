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

Given a roman numeral, convert it to an integer. Input is guaranteed to be within the range from 1 to 3999.

https://leetcode.com/problems/roman-to-integer/
"""

roman_numbers = {
    "M": 1000,
    "D": 500,
    "C": 100,
    "L": 50,
    "X": 10,
    "V": 5,
    "I": 1,
}


class Solution:
    def romanToInt(self, s: str) -> int:
        """ Assuming the incoming string is an actual roman number. """
        return_value = 0
        previous_value = None
        for symbol in s[::-1]:
            symbol_value = roman_numbers[symbol]
            if previous_value is None or previous_value <= symbol_value:
                return_value += symbol_value
            else:
                return_value -= symbol_value
            previous_value = symbol_value
        return return_value


test_cases = ["III", "IV", "IX", "LVIII", "MCMXCIV"]
results = [3, 4, 9, 58, 1994]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.romanToInt(test_case) == correct_result
        ), f"My result: {app.romanToInt(test_case)}, correct result: {correct_result}"
