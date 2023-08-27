from typing import List, Any, Generator
from math import factorial


def combination_generator(my_list: List[Any], n: int) -> Generator[Any, None, None]:
    if n == 0:
        yield []
    for i, middle in enumerate(my_list):
        middle = my_list[i]
        remaining_list = my_list[i + 1 :]
        for p in combination_generator(remaining_list, n - 1):
            yield [middle] + p


class CombinationIterator:
    def __init__(self, characters: str, combinationLength: int):
        self.combination_generator = combination_generator(list(characters), combinationLength)
        self.index = 0
        n = len(characters)
        k = combinationLength
        self.amount = factorial(n) // (factorial(k) * factorial(n - k))

    def next(self) -> str:
        self.index += 1
        return "".join(next(self.combination_generator))

    def hasNext(self) -> bool:
        return self.index < self.amount


if __name__ == "__main__":
    app = CombinationIterator("abc", 2)
    assert app.hasNext() is True
    assert app.next() == "ab"
    assert app.hasNext() is True
    assert app.next() == "ac"
    assert app.hasNext() is True
    assert app.next() == "bc"
    assert app.hasNext() is False
    assert app.amount == 3
