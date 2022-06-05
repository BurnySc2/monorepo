from contextlib import suppress


def divide_through_zero(n: float):
    return n / 0


def main():
    with suppress(ZeroDivisionError):
        divide_through_zero(420)


if __name__ == '__main__':
    main()
