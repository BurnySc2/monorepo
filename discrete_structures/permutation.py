from typing import Generator, List, Any


def permutation(my_list: List[Any]) -> List[Any]:
    if len(my_list) == 0:
        return []
    if len(my_list) == 1:
        return [my_list]
    result = []
    for i in range(len(my_list)):
        middle = my_list[i]
        remaining_list = my_list[:i] + my_list[i + 1 :]
        for p in permutation(remaining_list):
            result.append([middle] + p)
    return result


def permutation_generator(my_list: List[Any]) -> Generator[Any, None, None]:
    if not my_list:
        return
    if len(my_list) == 1:
        yield my_list
        return
    for i, middle in enumerate(my_list):
        remaining_list = my_list[:i] + my_list[i + 1 :]
        for p in permutation_generator(remaining_list):
            yield [middle] + p


if __name__ == "__main__":
    data = list("123")

    for p in permutation(data):
        print(p)

    print("###################")

    for p in permutation_generator(data):
        print(p)
