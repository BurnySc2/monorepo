from typing import List, Optional

from loguru import logger
from sqlmodel import Field, Relationship, Session, SQLModel, create_engine, select


class Author(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    birth_year: int


class Publisher(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    founded_year: int


class Book(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    release_year: int
    author_id: Optional[int] = Field(default=None, foreign_key='author.id')
    author: Optional[Author] = Relationship()
    publisher_id: Optional[int] = Field(default=None, foreign_key='publisher.id')
    publisher: Optional[Publisher] = Relationship()


class Library(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    address: str
    # Each library owns certain books with a certain amount
    books: List['BookInventory'] = Relationship(back_populates='library')


class BookInventory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    book_id: Optional[int] = Field(default=None, foreign_key='book.id')
    book: Optional[Book] = Relationship()
    library_id: Optional[int] = Field(default=None, foreign_key='library.id')
    library: Optional[Library] = Relationship()
    amount: int


# pylint: disable=R0914
# pylint: disable=R0915
def test_database_with_sqlmodel_readme_example():
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

    engine = create_engine('sqlite:///:memory:')

    # 1) Create tables
    SQLModel.metadata.create_all(engine)

    # 2) Fill tables
    with Session(engine) as session:
        for row in [
            author_1, author_2, author_3, publisher_1, publisher_2, publisher_3, book_1, book_2, book_3, book_4,
            library_1, library_2
        ]:
            session.add(row)
        session.commit()

    # 3) Select books
    with Session(engine) as session:
        statement = select(Book).where(Book.release_year < 1960)
        books = session.exec(statement)
        for book in books:
            logger.info(f'Found books released before 1960: {book}')

    # 4) Update books
    with Session(engine) as session:
        statement = select(Book).where(Book.release_year < 1960)
        books = session.exec(statement)
        for book in books:
            logger.info(f'Changing release year on book: {book}')
            book.release_year = 1970
        session.commit()

    # 5) Delete books
    with Session(engine) as session:
        statement = select(Book).where(Book.name == 'This book was not written')
        books = session.exec(statement)
        for book in books:
            logger.info(f'Removing book: {book}')
            session.delete(book)
        session.commit()

    # 6) Get data from other tables
    with Session(engine) as session:
        statement = select(Book)
        books = session.exec(statement)
        for book in books:
            logger.info(f'Book ({book}) has author ({book.author}) and publisher ({book.publisher})')

    with Session(engine) as session:
        statement = select(Library)
        libaries = session.exec(statement)
        for library in libaries:
            logger.info(f'Library ({library}) has books')
            for book_inventory in library.books:
                logger.info(f'    Book inventory ({book_inventory}) of book ({book_inventory.book})')

    # 7) Join two tables and apply filter
    # Find all books that are listed in libraries at least 25 times and where author was born before 1910
    with Session(engine) as session:
        statement = select(
            BookInventory,
        ).join(
            Book,
        ).join(
            Author,
        ).where((BookInventory.amount >= 25) & (Author.birth_year < 1910))

        book_inventories = session.exec(statement)
        for book_inventory in book_inventories:
            logger.info(
                f'Book ({book_inventory.book}) is listed in ({book_inventory.library}) {book_inventory.amount} times and the author is ({book_inventory.book.author})'
            )


if __name__ == '__main__':
    test_database_with_sqlmodel_readme_example()
