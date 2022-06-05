from typing import Any, Generator, List

from python_examples.discrete_structures.product import product_generator


def combination_generator(my_list: List[Any], n: int) -> Generator[Any, None, None]:
    if n == 0:
        yield []
    for i, middle in enumerate(my_list):
        remaining_list = my_list[i + 1:]
        for p in combination_generator(remaining_list, n - 1):
            yield [middle] + p


def _is_sorted(my_list: List[Any]) -> bool:
    for current, next_value in zip(my_list, my_list[1:]):
        if current > next_value:
            return False
    return True


def combinations_with_replacement_generator(iterable: List[Any], replacement: int):
    pool = tuple(iterable)
    n = len(pool)
    for indices in product_generator(range(n), repeat=replacement):
        #  if sorted(indices) == list(indices):
        if _is_sorted(indices):
            yield tuple(pool[i] for i in indices)


if __name__ == '__main__':
    data = list('123')
    for p in combination_generator(data, 2):
        print(p)

    print('###################')

    for p in combinations_with_replacement_generator(data, 2):
        print(p)
