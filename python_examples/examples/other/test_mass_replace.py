from hypothesis import given
from hypothesis import strategies as st

from python_examples.examples.other.mass_replace import mass_replacer


def test_example_text():
    text = 'my text cond\nition1 condition2'
    replace_dict = {'cond\nition1': 'loves', 'condition2': 'fun'}

    new_text = mass_replacer(text, replace_dict)
    assert new_text == 'my text loves fun'


@given(
    st.text(min_size=1),
    st.text(min_size=1),
    st.text(),
    st.text(),
)
def test_many_texts(
    w1: str,
    w2: str,
    w3: str,
    w4: str,
):
    if w1 == w2 or w1 in w2 or w2 in w1:
        # Unexpected behavior when both keys are the same
        # or one key is contained in the other
        return

    text = f'{w1}{w2}{w1}{w2}{w2}'
    replace_dict = {
        w1: w3,
        w2: w4,
    }
    new_text = mass_replacer(text, replace_dict)
    expected_text = f'{w3}{w4}{w3}{w4}{w4}'
    assert new_text == expected_text

    # The following may fail
    # new_text_with_replace1 = text.replace(w1, w2).replace(w3, w4)
    # assert new_text_with_replace1 == expected_text
    # new_text_with_replace2 = text.replace(w3, w4).replace(w1, w2)
    # assert new_text_with_replace2 == expected_text
