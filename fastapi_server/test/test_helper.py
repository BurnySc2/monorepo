import time
from string import ascii_lowercase, ascii_uppercase

import hypothesis.strategies as st
import pytest
from hypothesis import given, settings
from hypothesis.strategies import DataObject

from fastapi_server.helper.helper import get_username_from_token, hash_password, jwt_decode, jwt_encode, token_is_valid
from fastapi_server.test.base_test import BaseTest


class TestHelper(BaseTest):

    def test_jwt(self):
        my_data = {'some': 'data'}
        my_secret = 'supersecuresecret'
        jwt_token = jwt_encode(my_data, my_secret)
        decoded = jwt_decode(jwt_token, my_secret)
        assert my_data == decoded
        with pytest.raises(AssertionError):
            token_is_valid(jwt_token, my_secret)

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

    def test_jwt_is_valid(self):
        my_data = {'username': 'myname', 'expire_time': time.time() + 123.456}
        my_secret = 'supersecuresecret'
        jwt_token = jwt_encode(my_data, my_secret)
        assert token_is_valid(jwt_token, my_secret)
        assert get_username_from_token(jwt_token, my_secret) == 'myname'

    @settings(max_examples=200)
    @given(data=st.data())
    def test_jwt_is_valid_multiple(self, data: DataObject):
        username = data.draw(st.text())
        expire_time = data.draw(
            # Valid
            st.floats(allow_nan=False, allow_infinity=False, min_value=10)
            # Invalid, expire time before current time
            | st.floats(allow_nan=False, allow_infinity=False, max_value=0)
        )
        my_data = {'username': username, 'expire_time': time.time() + expire_time}
        my_secret = 'supersecuresecret'
        jwt_token = jwt_encode(my_data, my_secret)
        if expire_time > 0:
            assert token_is_valid(jwt_token, my_secret)
        else:
            assert not token_is_valid(jwt_token, my_secret)
        assert get_username_from_token(jwt_token, my_secret) == username
