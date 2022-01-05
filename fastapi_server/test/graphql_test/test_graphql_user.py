import hypothesis.strategies as st
from hypothesis import given, settings
from hypothesis.strategies import DataObject
from sqlalchemy import func
from sqlmodel import Session, select
from sqlmodel.sql.expression import SelectOfScalar
from starlette.testclient import TestClient

from fastapi_server.models.user import User
from fastapi_server.test.base_test import TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH, BaseTest


class TestGraphql(BaseTest):

    # def test_user_login_single(self, method_session_fixture: Session, method_client_fixture: TestClient):
    #     """ Single example to be able to debug into """
    #     assert method_session_fixture.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
    #     username = 'asd@gmail.com'
    #     email = 'asd@gmail.com'
    #     password = 'asd2'
    #     assert method_session_fixture.exec(select(User)).all() == []
    #     self.user_login(method_session_fixture, method_client_fixture, username, email, password)
    #     assert method_session_fixture.exec(select(User)).all() != []
    #
    # @settings(max_examples=200)
    # @given(data=st.data())
    # def test_user_login_multiple(self, data: DataObject):
    #     """ Multiple examples via hypothesis """
    #     # TODO: Chooser broader regex
    #     username = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
    #     email = data.draw(st.from_regex('[a-zA-Z]{1,20}@gmailcom', fullmatch=True))
    #     password = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
    #     client: TestClient = self.method_client
    #     session: Session = self.method_session
    #     assert session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
    #     self.user_login(session, client, username, email, password)
    #
    # @staticmethod
    # def user_login(session: Session, client: TestClient, username: str, email: str, password_plain: str):
    #     assert isinstance(session, Session)
    #     assert isinstance(client, TestClient)
    #     assert username is not None
    #     assert email is not None
    #     assert isinstance(email, str)
    #     assert email
    #     assert password_plain is not None
    #     username_taken = session.exec(select(User).where(User.username == username)).first()
    #     if username_taken is not None:
    #         return
    #     email_taken = session.exec(select(User).where(User.email == email)).first()
    #     if email_taken is not None:
    #         return
    #     session.add(
    #         User(
    #             username=username,
    #             email=email,
    #             password_hashed=hash_password(password_plain),
    #             is_admin=False,
    #             is_disabled=False,
    #             is_verified=False,
    #         )
    #     )
    #     session.commit()
    #     # assert session.exec(select(User)).all() != []
    #
    #     query = """
    #         query TestQuery ($email: String!, $password: String!) {
    #             userLogin(email: $email, passwordPlain: $password)
    #         }
    #     """
    #     response = client.post(
    #         '/graphql', json={
    #             'query': query,
    #             'variables': {
    #                 'email': email,
    #                 'password': password_plain
    #             }
    #         }
    #     )
    #     assert response.json() == {'data': {'userLogin': f'Login successful for {email}'}}

    def test_user_register_single(self, method_session_fixture: Session, method_client_fixture: TestClient):
        assert method_session_fixture.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
        username = 'asd@gmail.com'
        email = 'asd@gmail.com'
        password = 'asd2'
        password_repeated = 'asd2'
        assert method_session_fixture.exec(select(User)).all() == []
        self.user_register(method_session_fixture, method_client_fixture, username, email, password, password_repeated)
        assert method_session_fixture.exec(select(User)).all() != []

    @settings(max_examples=200)
    @given(data=st.data())
    def test_user_register_multiple(self, data: DataObject):
        """ Multiple examples via hypothesis """
        # TODO: Chooser broader regex
        username = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        email = data.draw(st.from_regex('[a-zA-Z]{1,20}@gmailcom', fullmatch=True))
        password = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        password_repeated = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        client: TestClient = self.method_client
        session: Session = self.method_session
        assert session.bind.url.database in {TEST_DB_FILE_PATH, TEST_DB_MEMORY_PATH}  # type: ignore
        self.user_register(session, client, username, email, password, password_repeated)

    @staticmethod
    def user_register(
        session: Session, client: TestClient, username: str, email: str, password: str, password_repeated: str
    ):
        count_statement: SelectOfScalar = select(func.count()).select_from(User)  # type: ignore
        before_count: int = session.exec(count_statement).first()  # type: ignore
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
        after_count: int = session.exec(count_statement).first()  # type: ignore
        user_added: bool = after_count - before_count == 1

        # Error cases
        json_data = response.json()
        if 'errors' in json_data:
            error = json_data['errors'][0]
            message = error['message']
            if message == "'username taken'":
                assert session.exec(select(User).where(User.username == username)).first() is not None
            elif message == "'email taken'":
                assert session.exec(select(User).where(User.email == email)).first() is not None
            elif message == "'not same pw'":
                assert password != password_repeated
            else:
                assert False, f'Cant think of other cases {json_data}'
            assert error['path'] == ['userRegister']
            assert not user_added
            return

        # Success case
        if password == password_repeated:
            assert response.json() == {'data': {'userRegister': True}}
            assert user_added
            return

        assert False, f'Cant think of other cases {response.json()}'
