# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import python_examples.examples.databases.sqlmodel_example


@given(
    id_=st.one_of(st.none(), st.integers()),
    name=st.text(),
    secret_name=st.text(),
    age=st.one_of(st.none(), st.integers()),
)
def test_fuzz_Hero(id_, name, secret_name, age):
    python_examples.examples.databases.sqlmodel_example.Hero(id=id_, name=name, secret_name=secret_name, age=age)
