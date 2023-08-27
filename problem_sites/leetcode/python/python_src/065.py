"""
https://leetcode.com/problems/valid-number/
"""
from string import digits, whitespace

PLUS_MINUS_SIGN = {"+", "-"}


class Solution:
    def isNumber(self, s: str) -> bool:
        s = s.strip()
        last_character = ""
        expect_number = True

        seen_number = False
        seen_exponent = False
        seen_sign = False
        seen_decimal_point = False
        for i in s:
            if i in whitespace:
                if seen_number or seen_exponent or seen_sign or seen_decimal_point:
                    return False
                continue
            elif i in ".":
                if seen_decimal_point or seen_exponent:
                    return False
                if seen_number:
                    expect_number = False
                seen_decimal_point = True
            elif i in PLUS_MINUS_SIGN:
                if (seen_sign or seen_decimal_point) and last_character != "e":
                    return False
                seen_sign = True
            elif i == "e":
                if seen_exponent or not seen_number or (seen_sign and not seen_number):
                    return False
                seen_decimal_point = True
                expect_number = True
                seen_exponent = True
                seen_sign = False
            elif i in digits:
                seen_number = True
                expect_number = False
                seen_sign = True
            else:
                return False
            last_character = i
        return not expect_number


# fmt: off
test_cases = ["0", " 0.1 ", "abc", "1 a", "2e10", " -90e3 ", "1e","e3", " 6e-1", "99e2.5", "53.5e93", "--6", "-+3", "95a54e53", ".0", "0.", ".-4", ".e1", "32.e-80123"]
results = [True, True, False, False, True, True, False, False, True, False, True, False, False, False, True, True, False, False, True]
# fmt: on

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_result = app.isNumber(test_case)
        assert (
            my_result == correct_result
        ), f"My result: {my_result}, correct result: {correct_result}\nTest Case: {test_case}"
