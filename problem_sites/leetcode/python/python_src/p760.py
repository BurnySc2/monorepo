from dataclasses import dataclass
import math


@dataclass
class Formula:
    m: int
    n: int

    def __str__(self):
        return f"g({self.m}, {self.n}) = {self.m} ^ {self.n} + {self.m} | {self.n} + {self.m} & {self.n} == {self.compute()}"

    def compute(self) -> int:
        return self.m | self.n


def sum_formula(n: int) -> int:
    return n * (n + 1) // 2


def sum_formula_general(a: int, d: float, n: int) -> int:
    """
    SUM k=0 to n-1 of (a + k*d)
    = n/2 (2a + (n-1)d)
    https://www.mathsisfun.com/algebra/sequences-sums-arithmetic.html
    a = first term
    d = difference between terms
    n = amount of terms
    """
    assert n > 0, n
    return n * (2 * a + int((n - 1) * d)) // 2


def sum_formula_general_from_zero(d: int, n: int) -> int:
    """
    SUM k=0 to n-1 of (k*d)
    = n/2 ((n-1)d)
    https://www.mathsisfun.com/algebra/sequences-sums-arithmetic.html
    d = difference between terms
    n = amount of terms
    """
    assert n > 0, n
    return n * (n - 1) * d // 2


def calc_avg(start: float, end: float) -> float:
    if isinstance(start, int) and isinstance(end, int) and (start + end) % 2 == 0:
        return (start + end) // 2
    return (start + end) / 2


def compute_fastest(N: int) -> int:
    my_sums = {}
    half_power_of_two = 1
    power_of_two = 1

    for _ in range(int(math.log(N, 2)) + 1):
        power_of_two *= 2
        terms_amount, max_remainder = divmod(N, power_of_two)

        top_correction = 0
        bottom_correction = 0

        # TOP CALCULATION - remainder 0 to half_power_of_two
        top1_increment = power_of_two - 1
        top1 = calc_avg(2 * top1_increment, 2 * top1_increment * (terms_amount - 1))
        top2_increment = half_power_of_two
        top2 = calc_avg(2 * top2_increment, 2 * top2_increment * (terms_amount - 1))

        amount_12_terms = half_power_of_two
        top12 = calc_avg(top1 * amount_12_terms * (terms_amount - 1), top2 * amount_12_terms * (terms_amount - 1))
        result12 = top12

        if 0 <= max_remainder < power_of_two:
            top_correction_start = top1_increment * terms_amount
            increment = -terms_amount
            top12_correction_terms = half_power_of_two
            if 0 <= max_remainder < half_power_of_two:
                top12_correction_terms = max_remainder + 1
            top_correction = 2 * sum_formula_general(top_correction_start, increment, top12_correction_terms)

        # BOTTOM CALCULATION - remainder half_power_of_two to power_of_two
        bottom1_increment = half_power_of_two + 1
        bottom1 = calc_avg(4, 4 + 2 * bottom1_increment * (terms_amount - 1))
        bottom2_increment = power_of_two
        bottom2 = calc_avg(2 * bottom2_increment, 2 * bottom2_increment * terms_amount)

        bottom12 = calc_avg(bottom1 * amount_12_terms * terms_amount, bottom2 * amount_12_terms * terms_amount)
        result34 = bottom12

        if half_power_of_two <= max_remainder < power_of_two:
            bottom_correction_start = 2 + bottom1_increment * terms_amount
            increment = 2 + terms_amount
            bottom12_correction_terms = (max_remainder % half_power_of_two) + 1
            bottom_correction = 2 * sum_formula_general(bottom_correction_start, increment, bottom12_correction_terms)

        result = result12 + result34 + top_correction + bottom_correction
        my_sums[half_power_of_two] = result

        half_power_of_two = power_of_two
    corrected = {factor: factor * value for factor, value in my_sums.items() if isinstance(factor, int)}
    result = sum(corrected.values())
    return result


def compute_faster(N: int) -> int:
    debug_sums = {}
    my_sums = {}
    half_power_of_two = 1
    power_of_two = 1

    for _ in range(int(math.log(N, 2)) + 1):
        power_of_two *= 2
        start_value = 2
        terms_amount, max_remainder = divmod(N, power_of_two)
        for remainder in range(power_of_two):
            difference_between_terms = abs(half_power_of_two - remainder - 1) + half_power_of_two
            this_remainder_terms_amount = terms_amount + int(max_remainder >= remainder)
            if this_remainder_terms_amount == 0 or this_remainder_terms_amount == 1 and remainder < half_power_of_two:
                continue
            debug_sums[half_power_of_two] = debug_sums.get(half_power_of_two, {})
            debug_sums[half_power_of_two][remainder] = debug_sums[half_power_of_two].get(remainder, [])
            if remainder >= half_power_of_two:
                value = sum_formula_general(start_value, difference_between_terms, this_remainder_terms_amount)
                debug_sums[half_power_of_two][remainder].append(
                    f"E {start_value} {difference_between_terms} {this_remainder_terms_amount}"
                )
            else:
                value = sum_formula_general_from_zero(difference_between_terms, this_remainder_terms_amount)
                debug_sums[half_power_of_two][remainder].append(
                    f"E 0 {difference_between_terms} {this_remainder_terms_amount}"
                )
            debug_sums[half_power_of_two][remainder].append(value)
            my_sums[half_power_of_two] = my_sums.get(half_power_of_two, 0) + value
            if remainder >= half_power_of_two:
                start_value += 2
        half_power_of_two = power_of_two
    corrected = {factor: factor * value for factor, value in my_sums.items() if isinstance(factor, int)}
    result = 2 * sum(corrected.values())
    return result


def compute_slow(N: int) -> int:
    debug_sums = {}
    my_sums = {}
    half_power_of_two = 1
    power_of_two = 1

    for _ in range(int(math.log(N, 2)) + 1):
        power_of_two *= 2
        for number in range(half_power_of_two, N + 1):
            remainder = number % power_of_two
            factor_left = abs(half_power_of_two - remainder - 1) + half_power_of_two
            factor_right = number // power_of_two
            summand_after = 0
            if remainder >= half_power_of_two:
                summand_after = 2 * (remainder - half_power_of_two + 1)
            value = factor_left * factor_right + summand_after
            debug_sums[half_power_of_two] = debug_sums.get(half_power_of_two, {})
            debug_sums[half_power_of_two][remainder] = debug_sums[half_power_of_two].get(remainder, [])
            debug_sums[half_power_of_two][remainder].append(value)
            my_sums[half_power_of_two] = my_sums.get(half_power_of_two, 0) + value
        half_power_of_two = power_of_two
    corrected = {factor: factor * value for factor, value in my_sums.items() if isinstance(factor, int)}
    result = 2 * sum(corrected.values())
    return result


def main():
    my_sum = []
    target = 17

    # print g(k, n-k) triangle
    for n in range(target + 1):
        partial_sum = []
        for k in range(n + 1):
            a = Formula(k, n - k)
            partial_sum.append(a.compute())
        my_sum.append(partial_sum)

    print(f"g(k, n-k)")
    for row in my_sum:
        print(" ".join(map(str, row)))

    result_10 = compute_slow(10)
    result2_10 = compute_faster(10)
    result3_10 = compute_fastest(10)
    print(f"G(10) == {result_10}")
    print(f"G(10) == {result2_10}")
    print(f"G(10) == {result3_10}")

    result_100 = compute_slow(100)
    result2_100 = compute_faster(100)
    result3_100 = compute_fastest(100)

    print(f"G(100) == {result_100}")
    print(f"G(100) == {result2_100}")
    print(f"G(100) == {result3_100}")

    result_1000 = compute_slow(1000)
    result2_1000 = compute_faster(1000)
    result3_1000 = compute_fastest(1000)
    print(f"G(1000) == {result_1000}")
    print(f"G(1000) == {result2_1000}")
    print(f"G(1000) == {result3_1000}")

    assert result_10 == 754, f"{result_10} != 754"
    assert result_100 == 583_766, f"{result_100} != 583_766"
    assert result_1000 == 580_621_308, f"{result_1000} != 580_621_308"

    import time
    t1 = time.perf_counter()
    solution = compute_fastest(10**18) % 1_000_000_007
    t2 = time.perf_counter()
    print(f"{t2 - t1}")
    print(f"Solution: {solution}")


if __name__ == '__main__':
    main()
