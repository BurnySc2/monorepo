from unittest import TestCase

import hypothesis.strategies as st
from hypothesis import given, settings
from loguru import logger


class TestHypothesis(TestCase):
    """
    Setup and teardown happen as described in this file.
    You can verify this by running
    uv run pytest -s test/test_hypothesis.py
    """

    class_number = 0
    class_number_pytest = 0
    method_number_pytest = 0
    method_number = 0
    example_number = 0

    @classmethod
    def setUpClass(cls):
        logger.info("1) Setting up class1")
        cls.class_number += 1

    @classmethod
    def tearDownClass(cls):
        logger.info("Teardown class1")
        cls.class_number -= 1

    @classmethod
    def setup_class(cls):
        logger.info("2) Setting up class2")
        cls.class_number_pytest += 1

    @classmethod
    def teardown_class(cls):
        logger.info("Teardown class2")
        cls.class_number_pytest -= 1

    def setup_method(self, _method):
        logger.info("3) Setting up method1")
        self.method_number_pytest += 1

    def teardown_method(self, _method):
        logger.info("Teardown method1")
        self.method_number_pytest -= 1

    @classmethod
    def setUp(cls):
        logger.info("4) Setting up method2")
        cls.method_number += 1

    @classmethod
    def tearDown(cls):
        logger.info("Teardown method2")
        cls.method_number -= 1

    @classmethod
    def setup_example(cls):
        logger.info("5) Setting up example")
        cls.example_number += 1

    @classmethod
    def teardown_example(cls, _token=None):
        logger.info("Teardown example")
        cls.example_number -= 1

    @settings(max_examples=2)
    @given(_number=st.integers())
    def test_hypothesis(self, _number: int):
        assert self.class_number == 1, self.class_number
        assert self.class_number_pytest == 1, self.class_number_pytest
        assert self.method_number_pytest == 1, self.method_number_pytest
        assert self.method_number == 1, self.method_number
        assert self.example_number == 1, self.example_number
