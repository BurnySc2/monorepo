import re

from loguru import logger

from python_examples.examples.other.roman_numbers import generate_roman_number


def regex_match_test():
    """
    Match pattern:
    HH:MM:SS
    """
    assert re.fullmatch(r'(\d{2}):(\d{2}):(\d{2})', '00:00:00')
    assert not re.fullmatch(r'(\d{2}):(\d{2}):(\d{2})', '0:00:00')
    assert not re.fullmatch(r'(\d{2}):(\d{2}):(\d{2})', '00:0:00')
    assert not re.fullmatch(r'(\d{2}):(\d{2}):(\d{2})', '00:00:0')
    assert not re.fullmatch(r'(\d{2}):(\d{2}):(\d{2})', '00:0000')

    pattern = '^(1110)|(0111)$|(01110)|^(111)$'
    p = re.compile(pattern)

    assert p.search('111') and p.match('111')
    assert p.search('0111') and p.match('0111')
    # Why does it not match here?
    assert p.search('00111') and not p.match('00111')
    assert p.search('1110') and p.match('1110')
    assert p.search('01110') and p.match('01110')
    assert not p.search('011110') and not p.match('011110')
    assert not p.search('01111') and not p.match('01111')
    assert not p.search('11110') and not p.match('11110')

    pattern = '^(10)|(01)$|(010)|^(1)$'
    p = re.compile(pattern)
    # Why does it not match here?
    assert p.search('11101') and not p.match('11101')


def regex_match_roman_number(roman_number: str) -> bool:
    """Returns True if input string is a roman number
    First row: Look ahead -> dont match empty string
    Second row: 1000-3000
    Third row: 3400 or 3900, connected with 100, 200, 300, or 500, 600, 700 or 800
    Same pattern for 4th and 5th row
    """
    numbers_1_to_3999 = """
    (?=[MDCLXVI])
        M{0,3}
            ( C[MD] | D?C{0,3} )
                ( X[CL] | L?X{0,3} )
                    ( I[XV] | V?I{0,3} )
    """.replace(' ', '').replace('\n', '')
    return bool(re.fullmatch(numbers_1_to_3999, roman_number))


def test_all_roman_numbers():
    for i in range(1, 4000):
        assert regex_match_roman_number(generate_roman_number(i)), f'{generate_roman_number(i)} != {i}'
        if i == 3999:
            logger.info(f'3999 in roman number is: {generate_roman_number(i)}')
