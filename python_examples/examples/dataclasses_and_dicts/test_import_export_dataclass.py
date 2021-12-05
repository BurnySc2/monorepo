# This test code was written by the `hypothesis.extra.ghostwriter` module
# and is provided under the Creative Commons Zero public domain dedication.

from hypothesis import given
from hypothesis import strategies as st

import python_examples.examples.dataclasses_and_dicts.import_export_dataclass
from python_examples.examples.dataclasses_and_dicts.import_export_dataclass import MyDataClass


@given(name=st.text(), value=st.integers(), other=st.sets(st.integers()))
def test_fuzz_MyDataClass(name, value, other):
    python_examples.examples.dataclasses_and_dicts.import_export_dataclass.MyDataClass(
        name=name, value=value, other=other
    )


@given(
    some_dataclasses=st.lists(st.builds(MyDataClass)),
    other_dataclasses=st.lists(st.builds(MyDataClass)),
)
def test_fuzz_MyDataClassList(some_dataclasses, other_dataclasses):
    python_examples.examples.dataclasses_and_dicts.import_export_dataclass.MyDataClassList(
        some_dataclasses=some_dataclasses, other_dataclasses=other_dataclasses
    )
