from __future__ import annotations

from datetime import datetime

from hypothesis import given
from hypothesis import strategies as st
from pydantic import BaseModel, EmailStr, validator


class CreditCardModel(BaseModel):
    card_number: int


class PetModel(BaseModel):
    name: str
    type: str


class CatModel(PetModel):
    type: str = "cat"

    @validator("type")
    def type_must_be_cat(cls, v: str):
        assert v == "cat", "Must be cat"
        return v


class DogModel(PetModel):
    type: str = "dog"

    @validator("type")
    def type_must_be_dog(cls, v: str):
        assert v == "dog", "Must be dog"
        return v


class PersonModel(BaseModel):
    name: str
    email: EmailStr
    credit_card: CreditCardModel
    birthday: datetime
    password1: str
    password2: str
    # pets: List[PetModel]
    pets: list[CatModel | DogModel | PetModel]

    @validator("name")
    def name_must_contain_space(cls, v: str):
        assert " " in v, "Must contain a space"
        return v.title()  # Format the string to "Title Case"

    @validator("email")
    def email_must_contain_at(cls, v: EmailStr):
        assert "@" in v, "Must contain a @ symbol"
        return v

    @validator("password1")
    def password_longer_than_6(cls, v: str):
        assert len(v) > 6, "Password is too short"
        return v

    @validator("password2")
    def passwords_match(cls, v: str, values: dict):
        # if 'password1' in values and v == values['password1']:
        #     raise ValueError('Passwords do not match')
        assert "password1" in values and v == values["password1"], "Passwords do not match"
        return v


def test_pydantic():
    person = PersonModel(
        name="This works",
        email=EmailStr("some@email.com"),
        # Also works:
        # credit_card={"card_number": 123456},
        credit_card=CreditCardModel(card_number=123456),
        birthday=datetime(1234, 1, 1),
        password1="hunter2",
        password2="hunter2",
        pets=[
            PetModel(name="Parrot", type="parrot"),
            CatModel(name="Kitty"),
            DogModel(name="Peter"),
        ],
    )

    my_json = person.json()
    person2 = PersonModel.parse_raw(my_json)
    # Order matters in "List[Union[CatModel, DogModel, PetModel]]" so it tries to match cat and dog model first
    assert person == person2


@given(st.builds(CreditCardModel))
def test_property(_instance):
    pass
