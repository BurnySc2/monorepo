import sqlite3

from loguru import logger


# pylint: disable=R0914
# pylint: disable=R0915
def test_database_with_sqlite_readme_example():
    # with sqlite3.connect("example.db") as db:
    with sqlite3.connect(':memory:') as db:
        # Instead of returning tuples, return dicts https://stackoverflow.com/a/55986968
        db.row_factory = sqlite3.Row

        # 1) Create tables
        db.execute(
            'CREATE TABLE IF NOT EXISTS author (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, birth_year INTEGER)',
        )
        db.execute(
            'CREATE TABLE IF NOT EXISTS publisher (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, founded_year INTEGER)',
        )
        db.execute(
            '''CREATE TABLE IF NOT EXISTS book (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            release_year INTEGER,
            author_id INTEGER,
            publisher_id INTEGER,
            FOREIGN KEY(author_id) REFERENCES author(author_id),
            FOREIGN KEY(publisher_id) REFERENCES publisher(publisher_id)
            )''',
        )
        db.execute(
            '''CREATE TABLE IF NOT EXISTS library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            address TEXT
            )''',
        )
        db.execute(
            '''CREATE TABLE IF NOT EXISTS bookinventory (
            book_id INTEGER,
            library_id INTEGER,
            amount INTEGER,
            PRIMARY KEY (book_id, library_id),
            FOREIGN KEY(book_id) REFERENCES book(book_id),
            FOREIGN KEY(library_id) REFERENCES library(library_id)
            )''',
        )

        # 2) Fill tables
        tolkien_id = 1
        lee_id = 2
        orwell_id = 3
        authors = [
            (tolkien_id, 'J. R. R. Tolkien', 1892),
            (lee_id, 'Harper Lee', 1926),
            (orwell_id, 'George Orwell', 1903),
        ]
        db.executemany('INSERT INTO author (id, name, birth_year) VALUES (?, ?, ?)', authors)

        aufbau_id = 1
        hoffmann_id = 2
        heyne_id = 3
        publishers = [
            (aufbau_id, 'Aufbau-Verlag', 1945),
            (hoffmann_id, 'Hoffmann und Campe', 1781),
            (heyne_id, 'Heyne Verlag', 1934),
        ]
        db.executemany('INSERT INTO publisher (id, name, founded_year) VALUES (?, ?, ?)', publishers)

        book_id_1 = 1
        book_id_2 = 2
        book_id_3 = 3
        book_id_4 = 4
        books = [
            (book_id_1, 'The Lord of the Rings', 1954, tolkien_id, hoffmann_id),
            (book_id_2, 'To kill a Mockingbird', 1960, lee_id, aufbau_id),
            (book_id_3, 'Nineteen Eighty-Four', 1949, orwell_id, heyne_id),
            (book_id_4, 'This book was not written', 2100, orwell_id, heyne_id),
        ]
        db.executemany(
            'INSERT INTO book (id, name, release_year, author_id, publisher_id) VALUES (?, ?, ?, ?, ?)', books
        )

        library_id_1 = 1
        library_id_2 = 2
        libraries = [
            (library_id_1, 'New York Public Library', '224 East 125th Street'),
            (library_id_2, 'California State Library', '900 N Street'),
        ]
        db.executemany('INSERT INTO library (id, name, address) VALUES (?, ?, ?)', libraries)

        books_inventory = [
            (book_id_2, library_id_1, 15),
            (book_id_3, library_id_1, 40),
            (book_id_1, library_id_2, 25),
            (book_id_2, library_id_2, 30),
        ]
        db.executemany('INSERT INTO bookinventory (book_id, library_id, amount) VALUES (?, ?, ?)', books_inventory)

        # 3) Select books
        results: sqlite3.Cursor = db.execute(
            'SELECT id, name, author_id, publisher_id FROM book WHERE release_year < 1960',
        )
        for book in results:
            book_as_dict = dict(book)
            logger.info(f'Found books released before 1960: {book_as_dict}')

        # 4) Update books
        db.execute('UPDATE book SET release_year=1970 WHERE release_year < 1960')

        # 5) Delete books
        db.execute("DELETE FROM book WHERE name == 'This book was not written'")

        # 6) Get data from other tables
        results: sqlite3.Cursor = db.execute(
            """SELECT
            book.id, book.name, book.release_year, author_id, publisher_id,
            a.name AS author_name, a.birth_year, p.name AS publisher_name, p.founded_year
            FROM book
            JOIN author a on book.author_id = a.id
            JOIN publisher p on book.publisher_id = p.id""",
        )
        for row in results:
            row_as_dict = dict(row)
            logger.info(f'Book, author and publisher information: {row_as_dict}')

        # 7) Join two tables and apply filter
        # Find all books that are listed in libraries at least 25 times and where author was born before 1910
        results: sqlite3.Cursor = db.execute(
            """SELECT
            bookinventory.library_id, bookinventory.book_id, bookinventory.amount,
            b.name, b.release_year, a.name AS author_name, a.birth_year,
            l.name AS library_name, l.address AS library_address
            FROM bookinventory
            JOIN book b on bookinventory.book_id = b.id
            JOIN author a on b.author_id = a.id
            JOIN library l on bookinventory.library_id = l.id
            WHERE bookinventory.amount >= 25 AND a.birth_year < 1910
            """,
        )
        for row in results:
            row_as_dict = dict(row)
            logger.info(f'Book, author and publisher information: {row_as_dict}')

        # 8) TODO: Run migration (verify and change table schema if necessary)

        # 9) Clear table
        db.execute('DELETE FROM bookinventory')


if __name__ == '__main__':
    test_database_with_sqlite_readme_example()
