def generate_roman_number(n: int) -> str:
    """
    Allowed roman numbers:
    IV, VI, IX, XI, XC, LC, XXXIX, XLI
    Disallowed:
    IIV, VIIII, XXXX, IXL, XIL
    """
    if n > 4000:
        raise ValueError(f'Input too big: {n}')
    number_list = [
        (1000, 'M'),
        (900, 'CM'),
        (500, 'D'),
        (400, 'CD'),
        (100, 'C'),
        (90, 'XC'),
        (50, 'L'),
        (40, 'XL'),
        (10, 'X'),
        (9, 'IX'),
        (5, 'V'),
        (4, 'IV'),
        (1, 'I'),
    ]
    string_as_list = []
    for divisor, character in number_list:
        if n >= divisor:
            count, n = divmod(n, divisor)
            string_as_list.extend(count * [character])
    return ''.join(string_as_list)
