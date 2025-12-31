# https://www.codewars.com/kata/5518a860a73e708c0a000027/train/python
def helper(a: int, b: int) -> int:
    if b == 0:
        return 1
    if b == 1:
        return a
    if a == 0:
        return 0
    r = a % 10
    if r == 0:
        return 100
    # Careful with n % 4
    #     6 ^ i = [1, 6, 36, 216, 1296, ...]
    if r == 6:
        if a == 1 and b == 1:
            return 6
        return 36
    # Alternating:
    #     1 ^ i = [1, 1, ...]
    #     4 ^ i = [1, 4,  16,  64,  256,  1024, 4096]
    #     5 ^ i = [1, 5,  25,  125, 625, 3125, ...]
    #     9 ^ i = [1, 9,  81,  729, ...]
    #    11 ^ i = [1, 11, 121, ...]
    #    15 ^ i = [1, 15, 225, ...]
    if r in {1, 4, 5, 9}:
        exponent = b % 2
        if b >= 2:
            exponent += 2
        return a ** exponent
    # Pattern every 4:
    #     2 ^ i = [1, 2, 4,  8,   16,   32,   64, 128, 256, 512, 1024, ...]
    #     3 ^ i = [1, 3, 9,  27,  81,   243,  729, ...]
    #     7 ^ i = [1, 7, 49, 343, 2301, ...]
    #     8 ^ i = [1, 8, 64, 512, 4096, ...]
    if r in {2, 3, 7, 8}:
        exponent = b % 4
        if b >= 4:
            exponent += 4
        return (a % 100) ** exponent

def last_digit(n1, n2):
    return helper(n1, n2) % 10
