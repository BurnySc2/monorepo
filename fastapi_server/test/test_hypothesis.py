import hypothesis.strategies as st
from hypothesis import given, settings


class TestHypothesis:
    class_number = 0

    @classmethod
    def setup_example(cls):
        cls.class_number += 1

    @classmethod
    def teardown_example(cls, _token=None):
        cls.class_number -= 1

    @settings(max_examples=100)
    @given(_number=st.integers())
    def test_hypothesis(self, _number: int):
        assert self.class_number == 1
