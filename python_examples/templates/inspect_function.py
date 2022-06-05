import inspect
from types import MappingProxyType
from typing import Callable


def func_without_arg() -> None:
    return None


def func_with_1_arg(value: int, optional: int = 0) -> int:
    return value + 1 + optional


def func_with_2_args(value1: int, value2: int, optional: int = 0, another_optional: int = 0) -> int:
    return value1 + value2 + optional + another_optional


def total_arg_count(func: Callable) -> int:
    return len(inspect.signature(func).parameters)


def required_arg_count(func: Callable) -> int:
    param_info: MappingProxyType[str, inspect.Parameter] = inspect.signature(func).parameters
    return sum(1 for param in param_info.values() if param.default is param.empty)


def optional_arg_count(func: Callable) -> int:
    param_info: MappingProxyType[str, inspect.Parameter] = inspect.signature(func).parameters
    return sum(1 for param in param_info.values() if param.default is not param.empty)


def main():
    assert total_arg_count(func_without_arg) == 0
    assert required_arg_count(func_without_arg) == 0
    assert optional_arg_count(func_without_arg) == 0

    assert total_arg_count(func_with_1_arg) == 2
    assert required_arg_count(func_with_1_arg) == 1
    assert optional_arg_count(func_with_1_arg) == 1

    assert total_arg_count(func_with_2_args) == 4
    assert required_arg_count(func_with_2_args) == 2
    assert optional_arg_count(func_with_2_args) == 2


if __name__ == '__main__':
    main()
