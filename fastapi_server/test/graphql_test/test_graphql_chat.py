# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from asyncio.queues import Queue

from hypothesis import given
from hypothesis import strategies as st

import fastapi_server.routes.graph_ql.graphql_chat


@given(subscribers=st.dictionaries(keys=st.text(), values=st.sets(st.builds(Queue))))
def test_broadcast(subscribers):
    fastapi_server.routes.graph_ql.graphql_chat.Broadcast(subscribers=subscribers)


@given(channel=st.text(), message=st.builds(object))
def test_broadcast_event(channel, message):
    fastapi_server.routes.graph_ql.graphql_chat.BroadcastEvent(channel=channel, message=message)


@given(timestamp=st.integers(), author=st.text(), message=st.text())
def test_chat_message(timestamp, author, message):
    fastapi_server.routes.graph_ql.graphql_chat.ChatMessage(timestamp=timestamp, author=author, message=message)


@given(timestamp=st.integers(), data=st.text())
def test_event(timestamp, data):
    fastapi_server.routes.graph_ql.graphql_chat.Event(timestamp=timestamp, data=data)


@given(queue=st.builds(Queue))
def test_fuzz_subscriber(queue):
    fastapi_server.routes.graph_ql.graphql_chat.Subscriber(queue=queue)
