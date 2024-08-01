from loguru import logger
from pony import orm  # pyre-fixme[21]

db = orm.Database()

# Create connection
db.bind(provider="sqlite", filename=":memory:")

# Write to file instead
# db.bind(provider='sqlite', filename='database.sqlite', create_db=True)
# PostgreSQL
# db.bind(provider='postgres', user='', password='', host='', database='')


# Create models
# pyre-fixme[11]
class Library(db.Entity):
    # "id" is autoinserted
    name = orm.Required(str)
    address = orm.Required(str)
    books = orm.Set("BookInventory")


class BookInventory(db.Entity):
    book = orm.Required("Book")
    library = orm.Required(Library)
    amount = orm.Required(int)


class Book(db.Entity):
    name = orm.Required(str)
    pages = orm.Required(int, py_check=lambda value: value > 0)
    release_year = orm.Required(int)
    author = orm.Required("Author")
    publisher = orm.Required("Publisher")
    book_inventories = orm.Set(BookInventory)

    def __repr__(self):
        return (
            f"Book(id={self.id}, author_id={self.author.id}, name='{self.name}', release_year={self.release_year}, "
            f"publisher_id={self.publisher.id})"
        )


class Author(db.Entity):
    name = orm.Required(str)
    birth_year = orm.Required(int)
    books = orm.Set(Book)


class Publisher(db.Entity):
    _table_ = "publisher"  # custom table name
    name = orm.Required(str)
    founded_year = orm.Required(int)
    books = orm.Set(Book)


def run_database_with_pony_readme_example():
    # Enable debug mode to see the queries sent
    orm.set_sql_debug(True)

    # 1) Create tables
    db.generate_mapping(create_tables=True)

    with orm.db_session():
        _tables = db.select(
            """
            * FROM information_schema.tables
            WHERE table_schema = 'public'
            """
        )
        _table_schema = db.select(
            """
                table_name,
                column_name,
                data_type
            FROM
                information_schema.columns
            WHERE
                table_name = 'Book';
            """
        )

    # 2) Fill tables
    with orm.db_session():
        # Autocommit after with-statement
        author_1 = Author(name="J. R. R. Tolkien", birth_year=1892)
        author_2 = Author(name="Harper Lee", birth_year=1926)
        author_3 = Author(name="George Orwell", birth_year=1903)

        publisher_1 = Publisher(name="Aufbau-Verlag", founded_year=1945)
        publisher_2 = Publisher(name="Hoffmann und Campe", founded_year=1781)
        publisher_3 = Publisher(name="Heyne Verlag", founded_year=1934)

        book_1 = Book(name="The Lord of the Rings", pages=1, release_year=1954, author=author_1, publisher=publisher_2)
        book_2 = Book(name="To kill a Mockingbird", pages=2, release_year=1960, author=author_2, publisher=publisher_1)
        book_3 = Book(name="Nineteen Eighty-Four", pages=3, release_year=1949, author=author_3, publisher=publisher_3)
        _book_4 = Book(
            name="This book was not written", pages=4, release_year=2100, author=author_3, publisher=publisher_3
        )

        library_1 = Library(name="New York Public Library", address="224 East 125th Street")
        library_inventory_1 = BookInventory(book=book_3, library=library_1, amount=40)
        library_inventory_2 = BookInventory(book=book_2, library=library_1, amount=15)
        library_1.books = [library_inventory_1, library_inventory_2]

        library_2 = Library(name="California State Library", address="900 N Street")
        library_inventory_3 = BookInventory(book=book_1, library=library_2, amount=25)
        library_inventory_4 = BookInventory(book=book_2, library=library_2, amount=30)
        library_2.books = [library_inventory_3, library_inventory_4]

    with orm.db_session():
        # 3) Select books
        # Selecting by id (any primary key) directly can be done with
        # book = Book[id]

        # Or by specific property, has to retrieve at most 1, is None if not in db
        # book = Book.get(name="This book was not written")

        # Both do the same
        # books = Book.select(lambda b: b.release_year < 1960).prefetch(Author, Publisher)
        books = (
            orm.select(b for b in Book if b.release_year < 1960)
            .prefetch(Author, Publisher)
            .order_by(
                orm.desc(Book.name),
                orm.desc(Book.pages),
            )[:10]
        )
        # with OR statement:
        # books = Book.select(lambda b: b.release_year < 1960 or "doesnt exist" in b.name).prefetch(Author, Publisher)
        for book in books:
            logger.info(f"Found books released before 1960: {book}")

        for book_name, book_pages in orm.select(
            (
                b.name,
                b.pages,
            )
            for b in Book
            if b.release_year < 1960
        ).order_by(-1, -2)[:10]:
            logger.info(f"Book name: '{book_name}' and pages count: {book_pages}")

    with orm.db_session():
        # Assert before
        books = Book.select(lambda b: b.release_year < 1960)
        assert len(books) == 2

        # 4) Update books
        for book in books:
            book.release_year = 1970

        # Assert after
        books = Book.select(lambda b: b.release_year < 1960)
        assert len(books) == 0

    with orm.db_session():
        # Assert before, is None if not found
        book = Book.get(name="This book was not written")
        assert book is not None

        # 5) Delete books
        book.delete()
        # orm.delete(b for b in Book if b.name == "This book was not written")

        # Assert after
        book = Book.get(name="This book was not written")
        assert book is None

    # 6) Get data from other tables
    with orm.db_session():
        # TODO
        pass

    # 7) Join two tables and apply filter

    # 8) TODO: Run migration (verify and change table schema if necessary)

    # 9) Clear table


if __name__ == "__main__":
    run_database_with_pony_readme_example()
