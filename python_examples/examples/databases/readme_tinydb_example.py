from dataclasses import dataclass
from typing import Iterable, Optional

from dataclasses_json import DataClassJsonMixin
from loguru import logger
from tinydb import Query, TinyDB, operations, where
from tinydb.storages import MemoryStorage


@dataclass
class Author(DataClassJsonMixin):
    name: str
    birth_year: int


@dataclass
class Publisher(DataClassJsonMixin):
    name: str
    founded_year: int


@dataclass
class Book(DataClassJsonMixin):
    name: str
    release_year: int
    author_id: Optional[int] = None
    publisher_id: Optional[int] = None


@dataclass
class Library(DataClassJsonMixin):
    name: str
    address: str


@dataclass
class BookInventory(DataClassJsonMixin):
    amount: int
    book_id: Optional[int] = None
    library_id: Optional[int] = None


def list_of_items_to_dict(items: Iterable[DataClassJsonMixin]) -> Iterable[dict]:
    return (i.to_dict() for i in items)


# pylint: disable=R0914
# pylint: disable=R0915
def test_database_with_tinydb():
    # Embedded pure-python dict based dictionary

    # Write to file:
    # db_path = Path(__file__).parent.parent.parent / 'data' / 'db.json'
    # os.makedirs(db_path.parent, exist_ok=True)
    # db = TinyDB(db_path)

    # Use in memory:
    db = TinyDB(storage=MemoryStorage)

    # 1) Create tables
    author_table = db.table('author')
    publisher_table = db.table('publisher')
    book_table = db.table('book')
    library_table = db.table('library')
    book_inventory_table = db.table('book_inventory')

    # 2) Fill tables
    author_1 = Author(name='J. R. R. Tolkien', birth_year=1892)
    author_2 = Author(name='Harper Lee', birth_year=1926)
    author_3 = Author(name='George Orwell', birth_year=1903)

    publisher_1 = Publisher(name='Aufbau-Verlag', founded_year=1945)
    publisher_2 = Publisher(name='Hoffmann und Campe', founded_year=1781)
    publisher_3 = Publisher(name='Heyne Verlag', founded_year=1934)

    author_id_1, author_id_2, author_id_3 = author_table.insert_multiple(
        list_of_items_to_dict([author_1, author_2, author_3])
    )
    publisher_id_1, publisher_id_2, publisher_id_3 = publisher_table.insert_multiple(
        list_of_items_to_dict([publisher_1, publisher_2, publisher_3])
    )

    book_1 = Book(name='The Lord of the Rings', release_year=1954, author_id=author_id_1, publisher_id=publisher_id_2)
    book_2 = Book(name='To kill a Mockingbird', release_year=1960, author_id=author_id_2, publisher_id=publisher_id_1)
    book_3 = Book(name='Nineteen Eighty-Four', release_year=1949, author_id=author_id_3, publisher_id=publisher_id_3)
    book_4 = Book(
        name='This book was not written', release_year=2100, author_id=author_id_3, publisher_id=publisher_id_3
    )
    book_id_1, book_id_2, book_id_3, _book_id_4 = book_table.insert_multiple(
        list_of_items_to_dict([book_1, book_2, book_3, book_4])
    )

    library_1 = Library(name='New York Public Library', address='224 East 125th Street')
    library_2 = Library(name='California State Library', address='900 N Street')
    library_id_1, library_id_2 = library_table.insert_multiple(list_of_items_to_dict([library_1, library_2]))

    library_inventory_1 = BookInventory(book_id=book_id_3, library_id=library_id_1, amount=40)
    library_inventory_2 = BookInventory(book_id=book_id_2, library_id=library_id_1, amount=15)
    library_inventory_3 = BookInventory(book_id=book_id_1, library_id=library_id_2, amount=25)
    library_inventory_4 = BookInventory(book_id=book_id_2, library_id=library_id_2, amount=30)
    book_inventory_table.insert_multiple(
        list_of_items_to_dict([library_inventory_1, library_inventory_2, library_inventory_3, library_inventory_4])
    )

    # Print all table names
    logger.info(db.tables())

    # 3) Select books
    query = Query()
    books = book_table.search(query.release_year < 1960)
    for book in books:
        logger.info(f'Found books released before 1960: {book}')

    # 4) Update books
    amount = book_table.count(where('release_year') < 1960)
    assert amount == 2, amount

    book_table.update({'release_year': 1970}, where('release_year') < 1960)

    amount = book_table.count(where('release_year') < 1960)
    assert amount == 0, amount

    # 5) Delete books
    amount = book_table.count(where('name') == 'This book was not written')
    assert amount == 1, amount

    book_table.remove(where('name') == 'This book was not written')

    amount = book_table.count(where('name') == 'This book was not written')
    assert amount == 0, amount

    # 6) Get data from other tables
    for book_raw in book_table:
        book = Book.from_dict(book_raw)
        author_raw = author_table.get(doc_id=book.author_id)
        author = Author.from_dict(author_raw)
        publisher_raw = publisher_table.get(doc_id=book.publisher_id)
        publisher = Publisher.from_dict(publisher_raw)
        logger.info(f'Book ({book}) has author ({author}) and publisher ({publisher})')

    for book_inventory_raw in book_inventory_table:
        book_inventory = BookInventory.from_dict(book_inventory_raw)
        library_raw = library_table.get(doc_id=book_inventory.library_id)
        library = Library.from_dict(library_raw)
        book_raw = book_table.get(doc_id=book_inventory.book_id)
        book = Book.from_dict(book_raw)
        logger.info(f'Library {library} has book inventory ({book_inventory}) of book ({book})')

    # 7) Join two tables and apply filter
    # Find all books that are listed in libraries at least 25 times and where author was born before 1910
    for book_inventory_raw in book_inventory_table.search(query.amount >= 25):
        book_inventory = BookInventory.from_dict(book_inventory_raw)
        book_raw = book_table.get(doc_id=book_inventory.book_id)
        book = Book.from_dict(book_raw)
        author_raw = author_table.get(doc_id=book.author_id)
        author = Author.from_dict(author_raw)
        if author.birth_year < 1910:
            library_raw = library_table.get(doc_id=book_inventory.library_id)
            library = Library.from_dict(library_raw)
            logger.info(f'Book {book} is listed in {library} {book_inventory.amount} times and the author is {author}')

    # 8) No need to migrate?
    # Remove key from each item in Author table if "birth_year" below 1910
    author_table.update(operations.delete('birth_year'), where('birth_year') < 1910)
    # Add a "death_year" if key "birth_year" exists
    author_table.update(operations.set('death_year', 2000), query.birth_year.exists())

    # 9) Clear table
    book_table.truncate()


if __name__ == '__main__':
    test_database_with_tinydb()
