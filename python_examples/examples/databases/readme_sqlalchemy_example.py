from typing import Iterable, List

from loguru import logger
from sqlalchemy import Column, ForeignKey, Integer, String, create_engine, delete
from sqlalchemy.orm import Query, Session, declarative_base, relationship
from sqlalchemy.sql import Delete

Base = declarative_base()


class MyBase:

    def __repr__(self) -> str:
        items = ', '.join(f'{key}={value}' for key, value in self.__dict__.items() if not key.startswith('_'))
        return f'{self.__class__.__name__}({items})'


class Author(Base, MyBase):  # type: ignore
    __tablename__ = 'author'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    birth_year = Column(Integer)


class Publisher(Base, MyBase):  # type: ignore
    __tablename__ = 'publisher'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    founded_year = Column(Integer)


class Book(Base, MyBase):  # type: ignore
    __tablename__ = 'book'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    release_year = Column(Integer)
    author_id = Column(ForeignKey('author.id'))
    author: Author = relationship('Author')  # type: ignore
    publisher_id = Column(ForeignKey('publisher.id'))
    publisher: Publisher = relationship('Publisher')  # type: ignore


class Library(Base, MyBase):  # type: ignore
    __tablename__ = 'library'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    address = Column(String)
    # Each library owns certain books with a certain amount
    books: List['BookInventory'] = relationship('BookInventory', back_populates='library')  # type: ignore


class BookInventory(Base, MyBase):  # type: ignore
    __tablename__ = 'book_inventory'
    id = Column(Integer, primary_key=True)
    book_id = Column(Integer, ForeignKey('book.id'))
    book: Book = relationship('Book')  # type: ignore
    library_id = Column(Integer, ForeignKey('library.id'))
    library: Library = relationship('Library')  # type: ignore
    amount = Column(Integer)


# pylint: disable=R0914
# pylint: disable=R0915
def test_database_with_sqlalchemy_readme_example():
    author_1 = Author(name='J. R. R. Tolkien', birth_year=1892)
    author_2 = Author(name='Harper Lee', birth_year=1926)
    author_3 = Author(name='George Orwell', birth_year=1903)

    publisher_1 = Publisher(name='Aufbau-Verlag', founded_year=1945)
    publisher_2 = Publisher(name='Hoffmann und Campe', founded_year=1781)
    publisher_3 = Publisher(name='Heyne Verlag', founded_year=1934)

    book_1 = Book(name='The Lord of the Rings', release_year=1954, author=author_1, publisher=publisher_2)
    book_2 = Book(name='To kill a Mockingbird', release_year=1960, author=author_2, publisher=publisher_1)
    book_3 = Book(name='Nineteen Eighty-Four', release_year=1949, author=author_3, publisher=publisher_3)
    book_4 = Book(name='This book was not written', release_year=2100, author=author_3, publisher=publisher_3)

    library_1 = Library(name='New York Public Library', address='224 East 125th Street')
    library_inventory_2 = BookInventory(book=book_2, library=library_1, amount=15)
    library_inventory_1 = BookInventory(book=book_3, library=library_1, amount=40)
    library_1.books = [library_inventory_1, library_inventory_2]

    library_2 = Library(name='California State Library', address='900 N Street')
    library_inventory_3 = BookInventory(book=book_1, library=library_2, amount=25)
    library_inventory_4 = BookInventory(book=book_2, library=library_2, amount=30)
    library_2.books = [library_inventory_3, library_inventory_4]

    engine = create_engine('sqlite+pysqlite:///:memory:', echo=False, future=True)

    # 1) Create tables
    Base.metadata.create_all(engine)

    # 2) Fill tables
    with Session(engine, autocommit=False) as session:
        session.add_all(
            [
                # Because library has references to the other objects, they automatically get added to the DB
                # author_1, author_2, author_3,
                # publisher_1, publisher_2, publisher_3,
                # book_1, book_2, book_3
                book_4,
                library_1,
                library_2
            ]
        )
        session.commit()

    # 3) Select books
    with Session(engine) as session:
        statement: Query = session.query(Book)
        result: Iterable[Book] = statement.filter(Book.release_year < 1960)
        for book in result:
            logger.info(f'Found books released before 1960: {book}')

    # 4) Update books
    with Session(engine) as session:
        assert session.query(Book).filter(Book.release_year < 1960).count() == 2
        statement: Query = session.query(Book)
        result: Iterable[Book] = statement.filter(Book.release_year < 1960)
        for book in result:
            logger.info(f'Changing release year on book: {book}')
            book.release_year = 1970
        assert session.query(Book).filter(Book.release_year < 1960).count() == 0
        session.commit()

    # 5) Delete books
    with Session(engine) as session:
        assert session.query(Book).filter(Book.name == 'This book was not written').count() == 1
        statement: Delete = delete(Book)
        statement: Delete = statement.where(Book.name == 'This book was not written')
        session.execute(statement)
        assert session.query(Book).filter(Book.name == 'This book was not written').count() == 0
        # Alternatively:
        # result: Iterable[Book] = query.filter(Book.name == 'This book was not written')
        # for book in result:
        #     session.delete(book)
        session.commit()

        query: Query = session.query(Book).filter(Book.name == 'This book was not written')
        assert query.first() is None, query.first()

    # 6) Get data from other tables
    with Session(engine) as session:
        statement: Query = session.query(Book)
        statement: Iterable[Book] = statement.join(Author).join(Publisher)
        for book in statement:
            logger.info(f'{book} has {book.author} and {book.publisher}')

    with Session(engine) as session:
        statement: Iterable[Library] = session.query(Library)
        for library in statement:
            logger.info(f'{library} has books:')
            for book_inventory in library.books:
                logger.info(f'    {book_inventory} of {book_inventory.book}')

    # 7) Join two tables and apply filter
    # Find all books that are listed in libraries at least 25 times and where author was born before 1910
    with Session(engine) as session:
        statement: Query = session.query(BookInventory)
        statement: Iterable[BookInventory] = statement.join(Book).join(Author).where(
            (BookInventory.amount >= 25) & (Author.birth_year < 1910)
        )
        for book_inventory in statement:
            logger.info(
                f'{book_inventory.book} is listed in {book_inventory.library} {book_inventory.amount} times and the author is ({book_inventory.book.author})'
            )

    # 8) TODO: Run migration (verify and change table schema if necessary)

    # 9) Clear table
    with Session(engine) as session:
        statement = delete(BookInventory)
        session.execute(statement)
        session.commit()


if __name__ == '__main__':
    test_database_with_sqlalchemy_readme_example()
