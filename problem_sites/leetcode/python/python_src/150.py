"""
Evaluate the value of an arithmetic expression in Reverse Polish Notation.

Valid operators are +, -, *, /. Each operand may be an integer or another expression.

https://leetcode.com/problems/evaluate-reverse-polish-notation/
"""


from typing import Set, Tuple, List, Generator, Dict
from operator import mul, add, sub
import math


class Solution:
    def evalRPN(self, tokens: List[str]) -> int:
        def floordiv(a, b):
            result = a / b
            if result >= 0:
                return int(result)
            return math.ceil(result)

        operators = {"+": add, "-": sub, "*": mul, "/": floordiv}

        index = 0
        while 1:
            token = tokens[index]
            if token in operators:
                first_value = tokens[index - 2]
                second_value = tokens[index - 1]
                operator: callable = operators[token]
                result = operator(int(first_value), int(second_value))
                # print(f"Doing operation: {first_value} {token} {second_value} = {result}")
                tokens[index] = result
                tokens.pop(index - 1)
                tokens.pop(index - 2)
                index -= 2
                # print(f"Index: {index}, tokens: {tokens}")
            index += 1
            if index >= len(tokens):
                break

        result = tokens[0]
        return result


test_cases = [
    ["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"],
    ["4", "13", "5", "/", "+"],
    [
        "-78",
        "-33",
        "196",
        "+",
        "-19",
        "-",
        "115",
        "+",
        "-",
        "-99",
        "/",
        "-18",
        "8",
        "*",
        "-86",
        "-",
        "-",
        "16",
        "/",
        "26",
        "-14",
        "-",
        "-",
        "47",
        "-",
        "101",
        "-",
        "163",
        "*",
        "143",
        "-",
        "0",
        "-",
        "171",
        "+",
        "120",
        "*",
        "-60",
        "+",
        "156",
        "/",
        "173",
        "/",
        "-24",
        "11",
        "+",
        "21",
        "/",
        "*",
        "44",
        "*",
        "180",
        "70",
        "-40",
        "-",
        "*",
        "86",
        "132",
        "-84",
        "+",
        "*",
        "-",
        "38",
        "/",
        "/",
        "21",
        "28",
        "/",
        "+",
        "83",
        "/",
        "-31",
        "156",
        "-",
        "+",
        "28",
        "/",
        "95",
        "-",
        "120",
        "+",
        "8",
        "*",
        "90",
        "-",
        "-94",
        "*",
        "-73",
        "/",
        "-62",
        "/",
        "93",
        "*",
        "196",
        "-",
        "-59",
        "+",
        "187",
        "-",
        "143",
        "/",
        "-79",
        "-89",
        "+",
        "-",
    ],
]
results = [22, 6, 165]

if __name__ == "__main__":
    app = Solution()
    for test_case, correct_result in zip(test_cases, results):
        my_solution = app.evalRPN(test_case)
        assert my_solution == correct_result, f"My result: {my_solution}, correct result: {correct_result}"
