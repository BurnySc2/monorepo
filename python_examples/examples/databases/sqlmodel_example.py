from typing import Optional

from loguru import logger
from sqlmodel import Field, Session, SQLModel, create_engine, or_, select


class Hero(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    secret_name: str = Field(max_length=30)
    age: Optional[int] = None


def test_database_with_sqlmodel():
    hero_1 = Hero(name='Deadpond', secret_name='Dive Wilson')
    hero_2 = Hero(name='Spider-Boy', secret_name='Pedro Parqueador')
    hero_3 = Hero(name='Rusty-Man', secret_name='Tommy Sharp', age=48)

    # engine = create_engine('sqlite:///temp.db')
    engine = create_engine('sqlite:///:memory:')

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        for hero in [hero_1, hero_2, hero_3]:
            session.add(hero)
        session.commit()

    with Session(engine) as session:
        statement = select(Hero).where(Hero.name == 'Spider-Boy')
        hero = session.exec(statement).first()
        logger.info(hero)

        # Or statement
        statement = select(Hero).where((Hero.name == 'Spider-Boy') | (Hero.name == 'Rusty-Man'))
        heroes = session.exec(statement)
        for hero in heroes:
            logger.info(hero)

        # Or statement, alternative way
        statement = select(Hero).where(or_(Hero.name == 'Spider-Boy', Hero.name == 'Rusty-Man'))
        heroes = session.exec(statement)
        for hero in heroes:
            logger.info(hero)

        # And statement
        statement = select(Hero).where(Hero.name == 'Spider-Boy', Hero.secret_name == 'Pedro Parqueador')
        heroes = session.exec(statement)
        for hero in heroes:
            logger.info(hero)

        # And statement, alternative way
        statement = select(Hero).where(Hero.name == 'Spider-Boy').where(Hero.secret_name == 'Pedro Parqueador')
        heroes = session.exec(statement)
        for hero in heroes:
            logger.info(hero)


if __name__ == '__main__':
    test_database_with_sqlmodel()
