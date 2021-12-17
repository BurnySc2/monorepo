"""
https://github.com/roman-right/beanie/
https://roman-right.github.io/beanie/
MongoDB GUI Interface: Robo 3T
"""
import asyncio
import sys
from typing import ForwardRef, List

import motor
from beanie import Document, init_beanie
from beanie.odm.operators.update.general import Set
from loguru import logger
from pydantic import Field
from pymongo.errors import ServerSelectionTimeoutError


# Queries can be cached https://roman-right.github.io/beanie/tutorial/cache/
class Author(Document):
    name: str
    birth_year: int


class Publisher(Document):
    name: str
    founded_year: int


class Book(Document):
    name: str
    release_year: int
    author: Author
    publisher: Publisher


# BookInventory is defined later so we have to use ForwardRef
ForwardRefBookInventory = ForwardRef('BookInventory')


class Library(Document):
    name: str
    address: str
    books: List[ForwardRefBookInventory] = Field(default_factory=list)  # type: ignore


class BookInventory(Document):
    amount: int
    book: Book
    library: Library


Library.update_forward_refs()


# pylint: disable=R0914
# pylint: disable=R0915
async def test_database_with_beanie():
    # Embedded pure-python dict based dictionary

    client = motor.motor_asyncio.AsyncIOMotorClient('mongodb://localhost:27017')

    # 1) Create tables
    try:
        await init_beanie(database=client.db_name, document_models=[Author, Publisher, Book, Library, BookInventory])
    except ServerSelectionTimeoutError:
        logger.error(
            "You can run mongodb by running: 'docker run --rm -d -p 27017-27019:27017-27019 --name mongodb mongo:5.0.0'",
        )
        sys.exit(1)

    # Clear for reuse
    await Book.find_all().delete()
    await Author.find_all().delete()
    await Publisher.find_all().delete()
    await Library.find_all().delete()
    await BookInventory.find_all().delete()

    # 2) Fill tables
    author_1 = Author(name='J. R. R. Tolkien', birth_year=1892)
    author_2 = Author(name='Harper Lee', birth_year=1926)
    author_3 = Author(name='George Orwell', birth_year=1903)
    await author_1.insert()
    # Alternatively:
    await author_2.create()
    await Author.insert_many([
        author_3,
    ])

    publisher_1 = Publisher(name='Aufbau-Verlag', founded_year=1945)
    publisher_2 = Publisher(name='Hoffmann und Campe', founded_year=1781)
    publisher_3 = Publisher(name='Heyne Verlag', founded_year=1934)
    await Publisher.insert_many([
        publisher_1,
        publisher_2,
        publisher_3,
    ])

    book_1 = Book(
        name='The Lord of the Rings',
        release_year=1954,
        author=await Author.find_one(Author.name == author_1.name),
        publisher=await Publisher.find_one(Publisher.name == publisher_1.name)
    )
    book_2 = Book(
        name='To kill a Mockingbird',
        release_year=1960,
        author=await Author.find_one(Author.name == author_2.name),
        publisher=await Publisher.find_one(Publisher.name == publisher_1.name)
    )
    book_3 = Book(
        name='Nineteen Eighty-Four',
        release_year=1949,
        author=await Author.find_one(Author.name == author_3.name),
        publisher=await Publisher.find_one(Publisher.name == publisher_3.name)
    )
    book_4 = Book(
        name='This book was not written',
        release_year=2100,
        author=await Author.find_one(Author.name == author_3.name),
        publisher=await Publisher.find_one(Publisher.name == publisher_3.name)
    )
    await Book.insert_many([
        book_1,
        book_2,
        book_3,
        book_4,
    ])

    library_1 = Library(name='New York Public Library', address='224 East 125th Street', books=[])
    library_2 = Library(name='California State Library', address='900 N Street', books=[])
    await library_1.save()
    await library_2.save()

    library_inventory_1 = BookInventory(
        book=await Book.find_one(Book.name == book_3.name),
        library=await Library.find_one(Library.name == library_1.name),
        amount=40
    )
    library_inventory_2 = BookInventory(
        book=await Book.find_one(Book.name == book_2.name),
        library=await Library.find_one(Library.name == library_1.name),
        amount=15
    )
    library_inventory_3 = BookInventory(
        book=await Book.find_one(Book.name == book_1.name),
        library=await Library.find_one(Library.name == library_2.name),
        amount=25
    )
    library_inventory_4 = BookInventory(
        book=await Book.find_one(Book.name == book_2.name),
        library=await Library.find_one(Library.name == library_2.name),
        amount=30
    )

    # Add library_inventory, which returns the inserted objects (or ids with insert_many
    library_inventory_1 = await library_inventory_1.save()
    library_inventory_2 = await library_inventory_2.save()
    # Add them to library_1.books
    library_1.books = [library_inventory_1, library_inventory_2]
    # Save changes
    _library_1 = await library_1.save()

    library_inventory_3 = await library_inventory_3.save()
    library_inventory_4 = await library_inventory_4.save()
    library_2.books = [library_inventory_3, library_inventory_4]
    _library_2 = await library_2.save()

    # 3) Select books
    # https://docs.mongoengine.org/guide/querying.html#query-operators
    async for book in Book.find(Book.release_year < 1960):  # pylint: disable=E1133
        logger.info(f'Found books released before 1960: {book}')
    # Alternatively with mongodb syntax
    # async for book in Book.find({"release_year": {"$lt": 1960}}):
    #     logger.info(f'Found books released before 1960: {book}')

    # 4) Update books
    assert await Book.find(Book.release_year < 1960).count() == 2
    await Book.find(Book.release_year < 1960).update(Set({Book.release_year: 1970}))
    # Alternatively with mongodb syntax
    # await Book.find({"release_year": {"$lt": 1960}}).update({"$set": {"release_year": 1970}})
    assert await Book.find(Book.release_year < 1960).count() == 0

    # 5) Delete books
    assert await Book.find(Book.name == 'This book was not written').count() == 1
    await Book.find(Book.name == 'This book was not written').delete()
    assert await Book.find(Book.name == 'This book was not written').count() == 0

    # 6) Get data from other tables
    async for book in Book.find_all():  # pylint: disable=E1133
        logger.info(f'Book ({book}) has author ({book.author}) and publisher ({book.publisher})')

    async for book_inventory in BookInventory.find_all():  # pylint: disable=E1133
        logger.info(
            f'Library {book_inventory.library} has book inventory ({book_inventory}) of book ({book_inventory.book})'
        )

    # 7) Join two tables and apply filter
    # Find all books that are listed in libraries at least 25 times and where author was born before 1910
    async for book_inventory in BookInventory.find( # pylint: disable=E1133
        BookInventory.amount <= 25,
        BookInventory.book.author.birth_year < 1910,
    ):
        logger.info(
            f'Book {book_inventory.book} is listed in {book_inventory.library} {book_inventory.amount} times and the author is {book_inventory.book.author}'
        )

    # 8) TODO: Migration

    # 9) Clear table
    await Book.find_all().delete()


if __name__ == '__main__':
    asyncio.run(test_database_with_beanie())
