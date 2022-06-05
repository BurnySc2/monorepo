import signal
import time
from contextlib import contextmanager
from platform import platform


class Timeout:
    """
    Run something for a maximum limited time
    try:
        with Timeout(seconds=2):
            ...
    except TimeoutError:
        ...
    """

    def __init__(self, seconds: int = 1, error_message='Timeout'):
        assert isinstance(seconds, int), type(seconds)
        assert seconds > 0
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, type_, value, traceback):
        signal.alarm(0)


@contextmanager
def timeout(seconds: int = 1, error_message='Timeout'):
    """
    Run something for a maximum limited time
    try:
        with Timeout(seconds=2):
            ...
    except TimeoutError:
    """
    assert isinstance(seconds, int), type(seconds)
    assert seconds > 0

    # SIGALRM doesn't work on windows
    if platform().startswith('win32'):
        yield
        return

    def timeout_handler(_signum, _frame):
        raise TimeoutError(error_message)

    signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)
    yield
    signal.alarm(0)


def main():
    # SIGALRM doesn't work on windows
    if platform().startswith('win32'):
        return

    # Test Timeout class
    try:
        with Timeout(seconds=1, error_message='Fancy error message'):
            time.sleep(3)
            assert False, 'Should never be reached'
    except TimeoutError:
        pass

    # Test timeout function with contextmanager
    try:
        with timeout(seconds=1, error_message='Fancy error message'):
            time.sleep(3)
            assert False, 'Should never be reached'
    except TimeoutError:
        pass


if __name__ == '__main__':
    main()
