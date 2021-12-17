from loguru import logger
from peewee import CharField, ForeignKeyField, IntegerField, Model, ModelSelect, SqliteDatabase

db = SqliteDatabase('test.db')


class Author(Model):
    name = CharField()
    birth_year = IntegerField()

    class Meta:
        database = db


class Publisher(Model):
    name = CharField()
    founded_year = IntegerField()

    class Meta:
        database = db


class Book(Model):
    name = CharField()
    release_year = IntegerField()
    author = ForeignKeyField(Author)
    publisher = ForeignKeyField(Publisher)

    class Meta:
        database = db

    def __str__(self):
        data = self.__dict__['__data__']
        items = ', '.join(f'{key}={value}' for key, value in data.items() if not key.startswith('_'))
        return f'{self.__class__.__name__}({items})'


class Library(Model):
    name = CharField()
    address = CharField()

    class Meta:
        database = db


class BookInventory(Model):
    book = ForeignKeyField(Book)
    library = ForeignKeyField(Library, backref='books')
    amount = IntegerField()

    class Meta:
        database = db


# pylint: disable=R0914
# pylint: disable=R0915
def test_database_with_peewee_readme_example():
    # 1) Create tables
    db.drop_tables([Book, Author, Publisher, Library, BookInventory])
    db.create_tables([Book, Author, Publisher, Library, BookInventory])

    # 2) Fill tables
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
    library_1.books = [library_inventory_1, library_inventory_2]  # pylint: disable=W0201

    library_2 = Library(name='California State Library', address='900 N Street')
    library_inventory_3 = BookInventory(book=book_1, library=library_2, amount=25)
    library_inventory_4 = BookInventory(book=book_2, library=library_2, amount=30)
    library_2.books = [library_inventory_3, library_inventory_4]  # pylint: disable=W0201

    assert Book.select().count() == 0, Book.select().count()  # pylint: disable=E1120
    assert Author.select().count() == 0, Author.select().count()  # pylint: disable=E1120
    assert Publisher.select().count() == 0, Publisher.select().count()  # pylint: disable=E1120
    assert Library.select().count() == 0, Library.select().count()  # pylint: disable=E1120
    assert BookInventory.select().count() == 0, BookInventory.select().count()  # pylint: disable=E1120
    for item in [
        author_1, author_2, author_3, publisher_1, publisher_2, publisher_3, book_1, book_2, book_3, book_4, library_1,
        library_2, library_inventory_1, library_inventory_2, library_inventory_3, library_inventory_4
    ]:
        item.save()
    assert Book.select().count() == 4, Book.select().count()  # pylint: disable=E1120
    assert Author.select().count() == 3, Author.select().count()  # pylint: disable=E1120
    assert Publisher.select().count() == 3, Publisher.select().count()  # pylint: disable=E1120
    assert Library.select().count() == 2, Library.select().count()  # pylint: disable=E1120
    assert BookInventory.select().count() == 4, BookInventory.select().count()  # pylint: disable=E1120

    # 3) Select books
    for book in Book.select().where(Book.release_year < 1960):  # pylint: disable=E1133
        logger.info(f'Found books released before 1960: {book}')

    # 4) Update books
    assert Book.select().where(Book.release_year < 1960).count() == 2
    for book in Book.select().where(Book.release_year < 1960):  # pylint: disable=E1133
        book.release_year = 1970
        book.save()
    assert Book.select().where(Book.release_year < 1960).count() == 0

    # 5) Delete books
    assert Book.select().where(Book.name == 'This book was not written').count() == 1
    Book.delete().where(Book.name == 'This book was not written').execute()
    assert Book.select().where(Book.name == 'This book was not written').count() == 0

    # 6) Get data from other tables
    for book in Book.select():
        logger.info(f'Book({book}) has Author({book.author}) and Publisher({book.publisher})')

    for library in Library.select():
        logger.info(f'Library ({library}) has books:')
        for book_inventory in library.books:
            logger.info(f'    Book inventory ({book_inventory}) of book ({book_inventory.book})')

    # 7) Join two tables and apply filter
    # Find all books that are listed in libraries at least 25 times and where author was born before 1910
    query: ModelSelect = BookInventory.select().join(Book).join(Author)
    query = query.where((BookInventory.amount >= 25) & (Author.birth_year < 1910))
    for book_inventory in query:
        logger.info(
            f'Book ({book_inventory.book}) is listed in ({book_inventory.library}) {book_inventory.amount} times and the author is ({book_inventory.book.author})'
        )

    # 8) TODO: Run migration (verify and change table schema if necessary)

    # 9) Clear table
    assert BookInventory.select().count() > 0  # pylint: disable=E1120
    BookInventory.delete().execute()  # pylint: disable=E1120
    assert BookInventory.select().count() == 0  # pylint: disable=E1120


if __name__ == '__main__':
    test_database_with_peewee_readme_example()
