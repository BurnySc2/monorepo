from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st

# pylint: disable=E0611
from pydantic import BaseModel, EmailStr, validator


class CreditCardMOdel(BaseModel):
    card_number: int


# pylint: disable=E0213
class PersonModel(BaseModel):
    name: str
    email: EmailStr
    credit_card: CreditCardMOdel
    birthday: datetime
    password1: str
    password2: str

    @validator('name')
    def name_must_contain_space(cls, v: str):
        assert ' ' in v, 'Must contain a space'
        return v.title()  # Format the string to "Title Case"

    @validator('email')
    def email_must_contain_at(cls, v: EmailStr):
        assert '@' in v, 'Must contain a @ symbol'
        return v

    @validator('password1')
    def password_longer_than_6(cls, v: str):
        assert len(v) > 6, 'Password is too short'
        return v

    @validator('password2')
    def passwords_match(cls, v: str, values: dict):
        # if 'password1' in values and v == values['password1']:
        #     raise ValueError('Passwords do not match')
        assert 'password1' in values and v == values['password1'], 'Passwords do not match'
        return v


def test_pydantic():
    person = PersonModel(
        name='This works',
        email=EmailStr('some@email.com'),
        # Also works:
        # credit_card={"card_number": 123456},
        credit_card=CreditCardMOdel(card_number=123456),
        birthday=datetime(1234, 1, 1),
        password1='hunter2',
        password2='hunter2',
    )

    my_json = person.json()
    person2 = PersonModel.parse_raw(my_json)
    assert person == person2


@given(st.builds(CreditCardMOdel))
def test_property(_instance):
    pass
