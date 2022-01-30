from string import ascii_lowercase, ascii_uppercase

import hypothesis.strategies as st
from hypothesis import given, settings
from hypothesis.strategies import DataObject

from fastapi_server.helper.helper import hash_password, jwt_decode, jwt_encode
from fastapi_server.test.base_test import BaseTest


class TestHelper(BaseTest):

    def test_jwt(self):
        my_data = {'some': 'data'}
        my_secret = 'supersecuresecret'
        jwt_token = jwt_encode(my_data, my_secret)
        decoded = jwt_decode(jwt_token, my_secret)
        assert my_data == decoded

    @settings(max_examples=200)
    @given(data=st.data())
    def test_jwt_multiple(self, data: DataObject):
        keys = st.text()
        values = st.floats(allow_nan=False) | st.integers() | st.text() | st.lists(st.text())
        my_data = data.draw(st.dictionaries(
            keys=keys,
            values=values,
        ))
        my_secret = data.draw(st.text())
        jwt_token = jwt_encode(my_data, my_secret)
        decoded = jwt_decode(jwt_token, my_secret)
        assert my_data == decoded

    def test_hash_password(self):
        my_plain_password = 'supersecurepassword'
        my_salt = (ascii_lowercase + ascii_uppercase)[:32].encode()
        password_hashed: str = hash_password(my_plain_password, my_salt)
        assert len(password_hashed) == 64
        assert password_hashed == 'e67dcd79181caf53a1316aa1fcf3e8f23e1ba4d9013b0d1128ba01b60924d621'

    @settings(max_examples=200)
    @given(data=st.data())
    def test_hash_password_multiple(self, data: DataObject):
        my_plain_password = data.draw(st.text())
        my_salt = data.draw(st.binary(min_size=32, max_size=32))
        password_hashed: str = hash_password(my_plain_password, my_salt)
        assert len(password_hashed) == 64
