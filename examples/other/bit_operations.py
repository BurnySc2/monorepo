import math
from dataclasses import dataclass

import hypothesis.strategies as st
from hypothesis import given


@dataclass()
class Float:
    sign: int
    exponent: int  # Decimal representation
    fraction: str

    def __post_init__(self):
        self._verify()

    def _verify(self):
        assert self.sign in {0, 1}
        assert 0 <= self.sign < 256
        assert len(self.fraction) == 23

    @staticmethod
    def from_float(number: float) -> 'Float':
        sign = int(number < 0)
        number = abs(number)
        exponent = math.floor(math.log2(number)) + 127
        number *= 2**(127 - exponent)
        number -= 1
        number *= 2**127
        fraction = '0' + bin(int(number))[2:24]
        # fraction.zfill(23)
        assert len(fraction) == 23
        return Float(sign, exponent, fraction)

    @staticmethod
    def from_string(number: str) -> 'Float':
        assert len(number) == 32
        sign = number[0]  # sign,     1 bit
        exponent = number[1:9]  # exponent, 8 bits
        fraction = number[9:]  # fraction, 23 bits
        return Float(int(sign), int(exponent, 2), fraction.zfill(23))

    def __float__(self) -> float:
        my_float = int('1' + self.fraction, 2) / 2**23
        return -1**self.sign * 2**(self.exponent - 127) * my_float

    def __str__(self) -> str:
        exponent_as_string = bin(self.exponent)[2:].zfill(8)
        return f'{self.sign} {exponent_as_string} {self.fraction.zfill(23)}'


def test_ieee754():
    N = '11000001101001001100000000000000'  # str of ieee-754 bits
    my_float = Float.from_string(N)
    assert -20.59375 == float(my_float)
    assert N == str(my_float).replace(' ', '')

    N2 = -20.59375
    my_float2 = Float.from_float(N2)
    print(float(my_float2))
    print(str(my_float2))
    assert -20.59375 == float(my_float2)
    assert N == str(my_float).replace(' ', '')


@given(st.floats())
def test_floats(x: float):
    assert x == float(Float.from_float(x))
