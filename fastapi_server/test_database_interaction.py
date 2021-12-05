# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import fastapi_server.database_interaction


@given(todo_description=st.text())
def test_fuzz_TodoItem(todo_description):
    fastapi_server.database_interaction.TodoItem(todo_description=todo_description)
