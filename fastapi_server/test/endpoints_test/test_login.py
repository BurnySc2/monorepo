import json
import time

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from hypothesis.strategies import DataObject

from fastapi_server.helper.helper import hash_password, jwt_decode
from fastapi_server.models.user import User
from fastapi_server.test.base_test import BaseTest


class TestUserLogin(BaseTest):

    def test_login_fail(self):
        with self.example_client_context() as client:
            with pytest.raises(FileNotFoundError):
                client.post('/login', data=json.dumps({
                    'email': 'admin',
                    'password': 'admin',
                }))

    def test_login_success(self):
        username = 'admin_user'
        email = 'admin'
        password = 'admin'
        with self.example_client_context() as client:
            # Add user
            session = self.example_session
            session.add(
                User(
                    username=username,
                    email=email,
                    password_hashed=hash_password(password),
                    is_admin=False,
                    is_disabled=False,
                    is_verified=False,
                )
            )
            session.commit()

            # Check user can login
            response = client.post('/login', data=json.dumps({
                'email': email,
                'password': password,
            }))
            assert response.status_code == 200
            cookies = client.cookies._cookies['testserver.local']['/']
            token: str = cookies['sessiontoken'].value
            token_data = jwt_decode(token)
            assert token_data['username'] == username
            assert token_data['expire_time'] > time.time()

    @settings(max_examples=20, deadline=2_000)
    @given(data=st.data())
    def test_login_success_multiple(self, data: DataObject):
        username = data.draw(st.text())
        email = data.draw(st.text())
        password = data.draw(st.text())
        with self.example_client_context() as client:
            # Add user
            session = self.example_session
            session.add(
                User(
                    username=username,
                    email=email,
                    password_hashed=hash_password(password),
                    is_admin=False,
                    is_disabled=False,
                    is_verified=False,
                )
            )
            session.commit()

            # Check user can login
            response = client.post('/login', data=json.dumps({
                'email': email,
                'password': password,
            }))
            assert response.status_code == 200
            # Check cookie exists and is ok
            cookies = client.cookies._cookies['testserver.local']['/']
            token: str = cookies['sessiontoken'].value
            token_data = jwt_decode(token)
            assert token_data['username'] == username
            assert token_data['expire_time'] > time.time()
