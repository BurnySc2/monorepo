import hypothesis.strategies as st
from hypothesis import given
from hypothesis.strategies import DataObject
from sqlmodel import Session

from fastapi_server.models.user import User
from fastapi_server.test.base_test import BaseTest


class TestDatabase(BaseTest):
    def test_user_add_single(self, session_fixture: Session):
        session = session_fixture
        username = 'asd'
        email = 'asd@gmail.com'
        password = 'asd2'
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

    @given(session=BaseTest.session_strategy(), my_schema=BaseTest.schema_strategy(), data=st.data())
    def test_user_add(self, session: Session, data: DataObject):
        username = data.draw(st.text())
        email = data.draw(st.emails())
        password = data.draw(st.text())
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
