class Solution:
    def reverse(self, x: int) -> int:
        if x == 0:
            return 0
        elif x < 0:
            return_value = -int(str(x)[1:][::-1])
        elif x > 0:
            return_value = int(str(x)[::-1])

        if min(x, return_value) < -(2 ** 31):
            return 0
        if max(x, return_value) > 2 ** 31 - 1:
            return 0
        return return_value
