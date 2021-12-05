# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import fastapi_server.routes.chat


@given(timestamp=st.floats(), author=st.text(), message=st.text())
def test_fuzz_ChatMessage(timestamp, author, message):
    fastapi_server.routes.chat.ChatMessage(timestamp=timestamp, author=author, message=message)
