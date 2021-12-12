# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from asyncio.queues import PriorityQueue

import pytest
from aiohttp.client import ClientSession
from hypothesis import given
from hypothesis import strategies as st

import python_examples.examples.async_await.rate_limited_example


@given(queue=st.builds(PriorityQueue))
@pytest.mark.asyncio
async def test_fuzz_create_tasks(queue):
    await python_examples.examples.async_await.rate_limited_example.create_tasks(queue=queue)


@given(
    session=st.builds(ClientSession),
    input_queue=st.builds(PriorityQueue),
    results=st.builds(list),
)
@pytest.mark.asyncio
async def test_fuzz_worker(session, input_queue, results):
    await python_examples.examples.async_await.rate_limited_example.worker(
        session=session, input_queue=input_queue, results=results
    )
