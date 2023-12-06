"""
Implement atoi which converts a string to an integer.

The function first discards as many whitespace characters as necessary until the first non-whitespace character is found. Then, starting from this character, takes an optional initial plus or minus sign followed by as many numerical digits as possible, and interprets them as a numerical value.

The string can contain additional characters after those that form the integral number, which are ignored and have no effect on the behavior of this function.

If the first sequence of non-whitespace characters in str is not a valid integral number, or if no such sequence exists because either str is empty or it contains only whitespace characters, no conversion is performed.

If no valid conversion could be performed, a zero value is returned.

https://leetcode.com/problems/string-to-integer-atoi/
"""


class Solution:
    def myAtoi(self, str: str) -> int:
        valid_characters = set("1234567890")
        return_list = []
        number_started = False

        for char in str:
            if not number_started and char in set(" +-"):
                return_list.append(char)
            elif char in valid_characters:
                return_list.append(char)
                number_started = True
            else:
                break

        return_str = "".join(return_list).strip()
        if not return_str:
            return 0
        try:
            return_number = int(return_str)
        except:
            return 0

        min_value = -(2 ** 31)
        max_value = 2 ** 31 - 1

        if return_number < min_value:
            return min_value
        if return_number > max_value:
            return max_value

        return return_number


test_cases = [
    "    -88827   5655  U",
    "  0000000000012345678",
    "42",
    "        -42",
    "4193 with words",
    "words and 987",
    "-91283472332",
]
results = [-88827, 12345678, 42, -42, 4193, 0, -2147483648]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        assert (
            app.myAtoi(test_case) == correct_result
        ), f"My result: {app.myAtoi(test_case)}, correct result: {correct_result}"
