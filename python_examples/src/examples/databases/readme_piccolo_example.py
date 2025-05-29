import asyncio
from pathlib import Path

from loguru import logger
from piccolo.columns import ForeignKey, Integer, Text
from piccolo.conf.apps import AppRegistry
from piccolo.engine.sqlite import SQLiteEngine
from piccolo.table import Table, create_db_tables

# Normally set in "piccolo_conf.py"
db_path = Path(__file__).parent / "temp.db"
DB = SQLiteEngine(path=db_path.absolute())
APP_REGISTRY = AppRegistry(apps=[])


class Author(Table, db=DB):
    name = Text(required=True)
    birth_year = Integer(required=True)


class Publisher(Table, db=DB):
    name = Text(required=True)
    founded_year = Integer(required=True)


class Book(Table, db=DB):
    name = Text(required=True)
    pages = Integer(required=True)
    release_year = Integer(required=True)
    author = ForeignKey(references=Author)
    publisher = ForeignKey(references=Publisher)


class Library(Table, db=DB):
    name = Text(required=True)
    address = Text(required=True)


class BookInventory(Table, db=DB):
    book = ForeignKey(references=Book)
    library = ForeignKey(references=Library)
    amount = Integer(required=True)


async def run_database_with_piccolo():
    # 1) Create tables
    tables = [Author, Publisher, Book, Library, BookInventory]
    await create_db_tables(*tables, if_not_exists=True)

    # 2) Fill tables
    authors = await Author.insert(
        Author(name="J. R. R. Tolkien", birth_year=1892),
        Author(name="Harper Lee", birth_year=1926),
        Author(name="George Orwell", birth_year=1903),
    ).returning(Author.id)
    publishers = await Publisher.insert(
        Publisher(name="Aufbau-Verlag", founded_year=1945),
        Publisher(name="Hoffmann und Campe", founded_year=1781),
        Publisher(name="Heyne Verlag", founded_year=1934),
    ).returning(Publisher.id)
    books = await Book.insert(
        Book(
            name="The Lord of the Rings",
            pages=1,
            release_year=1954,
            author=authors[0]["id"],
            publisher=publishers[1]["id"],
        ),
        Book(
            name="To kill a Mockingbird",
            pages=2,
            release_year=1960,
            author=authors[1]["id"],
            publisher=publishers[0]["id"],
        ),
        Book(
            name="Nineteen Eighty-Four",
            pages=3,
            release_year=1949,
            author=authors[2]["id"],
            publisher=publishers[2]["id"],
        ),
        Book(
            name="This book was not written",
            pages=4,
            release_year=2100,
            author=authors[2]["id"],
            publisher=publishers[2]["id"],
        ),
    ).returning(Book.id)
    library_1 = await Library(name="New York Public Library", address="224 East 125th Street").save()
    await BookInventory.insert(
        BookInventory(book=books[2]["id"], library=library_1[0]["id"], amount=40),
        BookInventory(book=books[1]["id"], library=library_1[0]["id"], amount=15),
    )

    library_2 = await Library(name="California State Library", address="900 N Street").save()
    await BookInventory.insert(
        BookInventory(book=books[0]["id"], library=library_2[0]["id"], amount=25),
        BookInventory(book=books[1]["id"], library=library_2[0]["id"], amount=30),
    )

    # 3) Select books
    query = (
        Book.objects()
        .where(Book.release_year < 1960)
        .order_by(Book.name, ascending=True)
        .order_by(Book.pages, ascending=False)
        .limit(10)
    )
    # Print resulting query:
    # print(query)
    books = await query
    for book in books:
        logger.info(f"Found books released before 1960: {book}")

    # Assert before
    books_before = await Book.count().where(Book.release_year < 1960)
    assert books_before == 2
    # 4) Update books
    for book in await Book.objects().where(Book.release_year < 1960):
        book.release_year = 1970
        await book.save()
    # Assert after
    books_after = await Book.count().where(Book.release_year < 1960)
    assert books_after == 0

    # Assert before, is None if not found
    book_before = await Book.objects().where(Book.name == "This book was not written").first()
    assert book_before is not None
    # 5) Delete books
    await Book.delete().where(Book.name == "This book was not written")
    # Assert after
    book_before = await Book.objects().where(Book.name == "This book was not written").first()
    assert book_before is None

    # 6) Get data from other tables
    books = await Book.objects()
    assert len(books) == 3
    # Attributes will only be integers in these cases because of no prefetch
    assert all(isinstance(book.author, int) and isinstance(book.publisher, int) for book in books)

    # Fetch data from author and publisher table
    books = await Book.objects(Book.author, Book.publisher)
    assert len(books) == 3
    assert all(isinstance(book.author, Author) and isinstance(book.publisher, Publisher) for book in books)

    # 7) Join two tables and apply filter on relational fields
    book_inventories = await BookInventory.objects(
        # Optional prefetch
        BookInventory.book,
        BookInventory.book.author,
        BookInventory.library,
    ).where(
        25 <= BookInventory.amount,
        BookInventory.book.author.birth_year < 1910,
    )
    print(book_inventories)
    assert len(book_inventories) == 2

    # 8) Alter table: Managed by CLI

    # 9) Delete all books
    assert await Book.count() == 3
    await Book.delete(force=True)
    assert await Book.count() == 0


if __name__ == "__main__":
    try:
        asyncio.run(run_database_with_piccolo())
    finally:
        # Clean up
        db_path.unlink(missing_ok=True)
