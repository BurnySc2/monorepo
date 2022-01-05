import hypothesis.strategies as st
from hypothesis import given
from hypothesis.strategies import DataObject
from sqlmodel import Session, select

from fastapi_server.models.user import User
from fastapi_server.test.base_test import BaseTest


class TestDatabase(BaseTest):

    def test_user_add_single(self, method_session_fixture: Session):
        session = method_session_fixture
        assert isinstance(session, Session)
        username = 'asd'
        email = 'asd@gmail.com'
        password = 'asd2'
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

    @given(data=st.data())
    def test_user_add_multiple(self, data: DataObject):
        username = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        email = data.draw(st.from_regex('[a-zA-Z]{1,20}@gmailcom', fullmatch=True))
        password = data.draw(st.from_regex('[a-zA-Z0-9]{1,20}', fullmatch=True))
        with self.example_session_context() as session:
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
