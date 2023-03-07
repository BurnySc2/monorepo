from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import given, settings


class TestHypothesis(TestCase):
    class_number = 0
    class_number_pytest = 0
    method_number = 0
    method_number_pytest = 0
    example_number = 0

    @classmethod
    def setUpClass(cls):
        cls.class_number += 1

    @classmethod
    def tearDownClass(cls):
        cls.class_number -= 1

    @classmethod
    def setup_class(cls):
        cls.class_number_pytest += 2

    @classmethod
    def teardown_class(cls):
        cls.class_number_pytest -= 2

    @classmethod
    def setUp(cls):
        cls.method_number += 3

    @classmethod
    def tearDown(cls):
        cls.method_number -= 3

    def setup_method(self, _method):
        self.method_number_pytest += 4

    def teardown_method(self, _method):
        self.method_number_pytest -= 4

    @classmethod
    def setup_example(cls):
        cls.example_number += 5

    @classmethod
    def teardown_example(cls, _token=None):
        cls.example_number -= 5

    @settings(max_examples=100)
    @given(_number=st.integers())
    def test_hypothesis(self, _number: int):
        assert self.class_number == 1, 'a'
        assert self.class_number_pytest == 2, 'b'
        assert self.method_number == 3, 'c'
        assert self.method_number_pytest == 4, 'd'
        assert self.example_number == 5, 'e'
