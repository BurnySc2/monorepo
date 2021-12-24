import hypothesis.strategies as st
from hypothesis import given
from hypothesis.strategies import DataObject
from sqlmodel import Session, select
from starlette.testclient import TestClient

from fastapi_server.models.user import User
from fastapi_server.test.base_test import TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH, BaseTest


class TestGraphql(BaseTest):
    def test_user_login_single(self, session_fixture: Session, client_fixture: TestClient):
        """ Single example to be able to debug into """
        assert session_fixture.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
        username = 'asd@gmail.com'
        email = 'asd@gmail.com'
        password = 'asd2'
        self.user_login(session_fixture, client_fixture, username, email, password)

    @given(data=st.data())
    def test_user_login_multiple_success(self, data: DataObject):
        """ Multiple examples via hypothesis """
        # TODO: Chooser broader regex
        username = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        email = data.draw(st.from_regex('[a-zA-Z]{1,20}@gmailcom', fullmatch=True))
        password = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        client: TestClient = data.draw(BaseTest.client_strategy())
        with BaseTest.session_context() as session:
            assert session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}
            self.user_login(session, client, username, email, password)

    @staticmethod
    def user_login(session: Session, client: TestClient, username: str, email: str, password: str):
        assert isinstance(session, Session)
        assert isinstance(client, TestClient)
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

    def test_user_register_single(self, session_fixture: Session, client_fixture: TestClient):
        assert session_fixture.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
        username = 'asd@gmail.com'
        email = 'asd@gmail.com'
        password = 'asd2'
        password_repeated = 'asd2'
        self.user_register(session_fixture, client_fixture, username, email, password, password_repeated)

    @given(data=st.data())
    def test_user_register_multiple(self, data: DataObject):
        """ Multiple examples via hypothesis """
        # TODO: Chooser broader regex
        username = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        email = data.draw(st.from_regex('[a-zA-Z]{1,20}@gmailcom', fullmatch=True))
        password = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        password_repeated = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        client: TestClient = data.draw(BaseTest.client_strategy())
        with BaseTest.session_context() as session:
            assert session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}
            self.user_register(session, client, username, email, password, password_repeated)

    @staticmethod
    def user_register(
        session: Session, client: TestClient, username: str, email: str, password: str, password_repeated: str
    ):
        assert session.exec(select(User)).all() == []
        query = """
            mutation TestMutation ($username: String!, $email: String!, $password: String!, $passwordRepeated: String!) {
                userRegister(username: $username, email: $email, password: $password, passwordRepeated: $passwordRepeated)
            }
        """
        response = client.post(
            '/graphql',
            json={
                'query': query,
                'variables': {
                    'username': username,
                    'email': email,
                    'password': password,
                    'passwordRepeated': password_repeated
                }
            }
        )
        if password == password_repeated:
            assert response.json() == {'data': {'userRegister': True}}
            assert session.exec(select(User)).all() != []
        else:
            errors = response.json()['errors'][0]
            assert errors['message'] == "'not same pw'"
            assert errors['path'] == ['userRegister']
            assert session.exec(select(User)).all() == []
