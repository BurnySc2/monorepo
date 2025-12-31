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

def last_digit(lst: list[int]) -> int:
    if not lst:
        return 1
    if len(lst) == 1:
        return lst[0] % 10
    if len(lst) == 2:
        return helper(lst[0], lst[1]) % 10

    base = lst[-2]
    exponent = lst.pop()
    lst[-1] = helper(base, exponent)
    return last_digit(lst)

if __name__ == "__main__":
    for a in range(0, 100):
        for b in range(0, 100):
            assert last_digit([a, b]) == (a ** b) % 10, print(f"{last_digit([a, b])} != {(a ** b) % 10}")

    assert last_digit([]) == 1
    assert last_digit([0, 0]) == 1
    assert last_digit([0, 0, 0]) == 0
    assert last_digit([1, 2]) == 1
    assert last_digit([3, 4, 5]) == 1
    assert last_digit([4, 3, 6]) == 4
    assert last_digit([7, 6, 21]) == 1
    assert last_digit([12, 30, 21]) == 6
    assert last_digit([2, 2, 2, 0]) == 4
    assert last_digit([937640, 767456, 981242]) == 0
    assert last_digit([123232, 694022, 140249]) == 6
    assert last_digit([499942, 898102, 846073]) == 6

    assert last_digit([98877, 201375, 113615]) == 3
    assert last_digit([2, 2, 101, 2]) == 6
    assert last_digit([7, 11, 2]) == 7
    assert last_digit([837142, 918895, 51096]) == 2
