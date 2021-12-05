# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from asyncio.queues import PriorityQueue

from aiohttp.client import ClientSession
from hypothesis import given
from hypothesis import strategies as st

import python_examples.examples.async_await.rate_limited_example


@given(queue=st.builds(PriorityQueue))
def test_fuzz_create_tasks(queue):
    python_examples.examples.async_await.rate_limited_example.create_tasks(queue=queue)


@given(
    session=st.builds(ClientSession),
    url=st.text(),
    retry=st.integers(),
    results=st.builds(list),
)
def test_fuzz_do_stuff(session, url, retry, results):
    python_examples.examples.async_await.rate_limited_example.do_stuff(
        session=session, url=url, retry=retry, results=results
    )


@given(
    session=st.builds(ClientSession),
    input_queue=st.builds(PriorityQueue),
    results=st.builds(list),
)
def test_fuzz_worker(session, input_queue, results):
    python_examples.examples.async_await.rate_limited_example.worker(
        session=session, input_queue=input_queue, results=results
    )
