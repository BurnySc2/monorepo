import warnings

warnings.simplefilter('once')


def context_level_2():
    warnings.warn(
        'With this stacklevel, the error will point to the call in context_level_1', DeprecationWarning, stacklevel=2
    )
    warnings.warn(
        'With this stacklevel, the error will point to the call in the main function', DeprecationWarning, stacklevel=3
    )


def context_level_1():
    context_level_2()


def main():
    # Warning will only be printed once
    context_level_1()
    # And not on a second call
    context_level_1()


if __name__ == '__main__':
    main()
