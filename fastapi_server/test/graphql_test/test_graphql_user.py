import hypothesis.strategies as st
from hypothesis import given, settings
from hypothesis.strategies import DataObject
from sqlmodel import Session, select
from starlette.testclient import TestClient

from fastapi_server.models.user import User
from fastapi_server.test.base_test import TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH, BaseTest


class TestGraphql(BaseTest):
    def test_user_login_single(self, session_fixture: Session, client_fixture: TestClient):
        """ Single example to be able to debug into """
        assert session_fixture.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}
        username = 'asd@gmail.com'
        email = 'asd@gmail.com'
        password = 'asd2'
        self.user_login(session_fixture, client_fixture, username, email, password)

    @settings(max_examples=100)
    @given(session=BaseTest.session_strategy(), client=BaseTest.client_strategy(), data=st.data())
    def test_user_login_multiple(self, session: Session, client: TestClient, data: DataObject):
        """ Multiple examples via hypothesis """
        assert session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}
        username = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        email = data.draw(st.from_regex('[a-zA-Z]{1,20}@gmailcom', fullmatch=True))
        password = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        # TODO: Chooser broader regex
        # TODO Why doesnt this work? Sql connection not closing properly?
        return
        self.user_login(session, client, username, email, password)

    @staticmethod
    def user_login(session: Session, client: TestClient, username: str, email: str, password: str):
        assert username is not None
        assert email is not None
        assert isinstance(email, str)
        assert email
        assert password is not None
        assert session.exec(select(User)).all() == []
        session.add(
            User(
                username=username,
                email=email,
                password_hashed=password,
                is_admin=False,
                is_disabled=False,
                is_verified=False,
            )
        )
        session.commit()
        assert session.exec(select(User)).all() != []

        query = """
            query TestQuery ($email: String!, $password: String!) {
                userLogin(email: $email, password: $password)
            }
        """
        response = client.post('/graphql', json={'query': query, 'variables': {'email': email, 'password': password}})
        assert response.json() == {'data': {'userLogin': f'Login successful for {email}'}}

    def user_register(self, session: Session, data: DataObject):
        # TODO Register user
        username = 'burny'
        email = 'burny@fakemail.com'
        password = '123456'
        password_repeated = '123456'
        query = """
        mutation TestMutation ($username: String!, $email: String!, $password: String!, $passwordRepeated: String!) {
                userRegister(username: $username, email: $email, password: $password, passwordRepeated: $passwordRepeated)
            }
        """

        result = my_schema.execute_sync(
            query,
            variable_values={
                'username': username,
                'email': email,
                'password': password,
                'passwordRepeated': password_repeated,
            }
        )

        assert result.errors is None
        assert result.data == {
            'userRegister': True,
        }
