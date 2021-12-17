"""
https://github.com/MongoEngine/mongoengine
MongoDB GUI Interface: Robo 3T
"""
import sys

from loguru import logger
from mongoengine import Document, IntField, ListField, ReferenceField, StringField, connect
from pymongo.errors import ServerSelectionTimeoutError


class Author(Document):
    name = StringField(required=True)
    birth_year = IntField()


class Publisher(Document):
    name = StringField(required=True)
    founded_year = IntField()


class Book(Document):
    name = StringField(required=True)
    release_year = IntField()
    author = ReferenceField(Author)
    publisher = ReferenceField(Publisher)

    def __str__(self):
        # TODO
        items = ', '.join(f'{key}={value}' for key, value in self.__dict__.items() if not key.startswith('_'))
        return f'{self.__class__.__name__}({items})'


class Library(Document):
    name = StringField(required=True)
    address = StringField(required=True)
    books = ListField(ReferenceField('BookInventory'))


class BookInventory(Document):
    amount = IntField()
    book = ReferenceField(Book)
    library = ReferenceField(Library)


# pylint: disable=R0914
# pylint: disable=R0915
def test_database_with_mongoengine():
    # Embedded pure-python dict based dictionary

    # 1) Create tables
    connect('mongoengine_db')

    # Clear db
    try:
        for i in [Author, Publisher, Book, Library, BookInventory]:
            for j in i.objects:
                j.delete()
    except ServerSelectionTimeoutError:
        logger.error(
            "You can run mongodb by running: 'docker run --rm -d -p 27017-27019:27017-27019 --name mongodb mongo:5.0.0'",
        )
        sys.exit(1)

    # 2) Fill tables
    author_1 = Author(name='J. R. R. Tolkien', birth_year=1892)
    author_2 = Author(name='Harper Lee', birth_year=1926)
    author_3 = Author(name='George Orwell', birth_year=1903)

    publisher_1 = Publisher(name='Aufbau-Verlag', founded_year=1945)
    publisher_2 = Publisher(name='Hoffmann und Campe', founded_year=1781)
    publisher_3 = Publisher(name='Heyne Verlag', founded_year=1934)

    book_1 = Book(name='The Lord of the Rings', release_year=1954, author=author_1, publisher=publisher_1)
    book_2 = Book(name='To kill a Mockingbird', release_year=1960, author=author_2, publisher=publisher_1)
    book_3 = Book(name='Nineteen Eighty-Four', release_year=1949, author=author_3, publisher=publisher_3)
    book_4 = Book(name='This book was not written', release_year=2100, author=author_3, publisher=publisher_3)

    library_1 = Library(name='New York Public Library', address='224 East 125th Street')
    library_2 = Library(name='California State Library', address='900 N Street')

    library_inventory_1 = BookInventory(book=book_3, library=library_1, amount=40)
    library_inventory_2 = BookInventory(book=book_2, library=library_1, amount=15)
    library_inventory_3 = BookInventory(book=book_1, library=library_2, amount=25)
    library_inventory_4 = BookInventory(book=book_2, library=library_2, amount=30)

    for document in [
        author_1, author_2, author_3, publisher_1, publisher_2, publisher_3, book_1, book_2, book_3, book_4, library_1,
        library_2, library_inventory_1, library_inventory_2, library_inventory_3, library_inventory_4
    ]:
        document.save()

    # 3) Select books
    # https://docs.mongoengine.org/guide/querying.html#query-operators
    for book in Book.objects(release_year__lt=1960):
        logger.info(f'Found books released before 1960: {book}')

    # 4) Update books
    assert Book.objects(release_year__lt=1960).count() == 2
    for book in Book.objects(release_year__lt=1960):
        book.release_year = 1970
        book.save()
        logger.info(f'Found books released before 1960: {book}')
    assert Book.objects(release_year__lt=1960).count() == 0

    # 5) Delete books
    assert Book.objects(name='This book was not written').count() == 1
    Book.objects(name='This book was not written').delete()
    assert Book.objects(name='This book was not written').count() == 0

    # 6) Get data from other tables
    for book in Book.objects:
        logger.info(f'Book ({book}) has author ({book.author}) and publisher ({book.publisher})')

    for book_inventory in BookInventory.objects:
        logger.info(
            f'Library {book_inventory.library} has book inventory ({book_inventory}) of book ({book_inventory.book})'
        )

    # 7) Join two tables and apply filter
    # Find all books that are listed in libraries at least 25 times and where author was born before 1910
    for book_inventory in BookInventory.objects(amount__gte=25):
        if book_inventory.book.author.birth_year < 1910:
            logger.info(
                f'Book {book_inventory.book} is listed in {book_inventory.library} {book_inventory.amount} times and the author is {book_inventory.book.author}'
            )

    # 8) TODO: Migration

    # 9) Clear table
    Book.objects.delete()


if __name__ == '__main__':
    test_database_with_mongoengine()
