from loguru import logger
from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import Session, declarative_base


def test_database_with_sqlalchemy():
    # Declare tables https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_declaring_mapping.htm
    Base = declarative_base()

    class Customers(Base):
        __tablename__ = 'customers'
        id = Column(Integer, primary_key=True)

        name = Column(String)
        address = Column(String)
        email = Column(String)

    # Create engine https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_creating_session.htm
    engine = create_engine('sqlite+pysqlite:///:memory:', echo=False, future=True)
    # Create tables
    Base.metadata.create_all(engine)

    # Start session
    with Session(engine, autocommit=False) as session:
        # Insert new item https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_adding_objects.htm
        c1 = Customers(name='Ravi Kumar', address='Station Road Nanded', email='ravi@gmail.com')
        session.add(c1)

        # Add multiple
        session.add_all(
            [
                Customers(
                    name='Komal Pande',
                    address='Koti, Hyderabad',
                    email='komal@gmail.com',
                ),
                Customers(
                    name='Rajender Nath',
                    address='Sector 40, Gurgaon',
                    email='nath@gmail.com',
                ),
                Customers(
                    name='S.M.Krishna',
                    address='Budhwar Peth, Pune',
                    email='smk@gmail.com',
                ),
            ],
        )
        session.commit()

        # List all https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_using_query.htm
        result = session.query(Customers).all()
        row: Customers
        for row in result:
            logger.info(f'SQLAlchemy: Name: {row.name}, Address: {row.address}, Email: {row.email}')

        # Filtered result
        result2 = session.query(Customers).filter(Customers.name == 'Rajender Nath')
        for row in result2:
            logger.info(f'Filter result: Name: {row.name}, Address: {row.address}, Email: {row.email}')
