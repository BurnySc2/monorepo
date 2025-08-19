"""
This file poses as an example to test async code.
"""

import hypothesis.strategies as st
import pytest
import pytest_asyncio
from hypothesis import given, settings
from loguru import logger


class TestAsync:
    """
    Setup and teardown happen as described in this file.
    You can verify this by running
    uv run pytest -s test/test_async.py
    """

    class_fixture_async_variable = 0
    class_fixture_sync_variable = 0
    method_fixture_async_variable = 0
    method_fixture_sync_variable = 0
    example_fixture_sync_variable = 0

    @pytest_asyncio.fixture(scope="class", autouse=True)
    @classmethod
    async def class_fixture_async(cls):
        logger.info("1) Setting up class async")
        cls.class_fixture_async_variable += 1
        yield
        logger.info("Teardown class async")
        cls.class_fixture_async_variable -= 1

    @pytest.fixture(scope="class", autouse=True)
    @classmethod
    def class_fixture_sync(cls):
        logger.info("2) Setting up class sync")
        cls.class_fixture_sync_variable += 1
        yield
        logger.info("Teardown class sync")
        cls.class_fixture_sync_variable -= 1

    @pytest_asyncio.fixture(scope="function", autouse=True)
    @classmethod
    async def method_fixture_async(cls):
        logger.info("3) Setting up method async")
        cls.method_fixture_async_variable += 1
        yield
        logger.info("Teardown method async")
        cls.method_fixture_async_variable -= 1

    @pytest.fixture(scope="function", autouse=True)
    @classmethod
    def method_fixture_sync(cls):
        logger.info("4) Setting up method sync")
        cls.method_fixture_sync_variable += 1
        yield
        logger.info("Teardown method sync")
        cls.method_fixture_sync_variable -= 1

    @classmethod
    def setup_example(cls):
        # Setup code for hypothesis example. Does not work with async
        logger.info("5) Setting up example with hypothesis")
        cls.example_fixture_sync_variable += 1

    @classmethod
    def teardown_example(cls, _token=None):
        logger.info("Teardown example")
        cls.example_fixture_sync_variable -= 1

    @pytest.mark.parametrize("number", [1, 2, 3])
    @pytest.mark.asyncio
    async def test_my_examples(self, number: int) -> None:
        assert number in [1, 2, 3]

    @settings(max_examples=2)
    @given(_number=st.integers())
    @pytest.mark.asyncio
    async def test_my_function(self, _number: int) -> None:
        assert self.class_fixture_async_variable == 1
        assert self.class_fixture_sync_variable == 1
        assert self.method_fixture_async_variable == 1
        assert self.method_fixture_sync_variable == 1
        assert self.example_fixture_sync_variable == 1
