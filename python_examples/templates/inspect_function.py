import inspect


def func_without_arg() -> None:
    return None


def func_with_1_arg(n: int, optional: int = 0) -> int:
    return n + 1 + optional


def func_with_2_args(a: int, b: int, optional: int = 0) -> int:
    return a + b + optional


def main():
    assert len(inspect.signature(func_without_arg).parameters) == 0
    assert len(inspect.signature(func_with_1_arg).parameters) == 2
    assert len(inspect.signature(func_with_2_args).parameters) == 3


if __name__ == '__main__':
    main()
