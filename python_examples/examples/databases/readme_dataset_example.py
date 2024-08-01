# ruff: noqa: C408
import dataset  # pyre-fixme[21]
from loguru import logger


def run_database_with_dataset_readme_example():
    db: dataset.Database = dataset.connect("sqlite:///:memory:")
    # db = dataset.connect("sqlite:///data.db")

    # 1) Create tables
    # SKIP

    # 2) Fill tables
    author_table: dataset.Table = db["author"]
    author_1_id = author_table.insert({"name": "J. R. R. Tolkien", "birth_year": 1892})
    author_2_id = author_table.insert({"name": "Harper Lee", "birth_year": 1926})
    author_3_id = author_table.insert({"name": "George Orwell", "birth_year": 1903})

    publisher_table: dataset.Table = db["publisher"]
    publisher_1_id = publisher_table.insert({"name": "Aufbau-Verlag", "founded_year": 1945})
    publisher_2_id = publisher_table.insert({"name": "Hoffmann und Campe", "founded_year": 1781})
    publisher_3_id = publisher_table.insert({"name": "Heyne Verlag", "founded_year": 1934})

    book_table: dataset.Table = db["book"]
    book_1_id = book_table.insert(
        {
            "name": "The Lord of the Rings",
            "pages": 1,
            "release_year": 1954,
            "author_id": author_1_id,
            "publisher_id": publisher_1_id,
        },
    )
    book_2_id = book_table.insert(
        {
            "name": "To kill a Mockingbird",
            "pages": 2,
            "release_year": 1960,
            "author_id": author_2_id,
            "publisher_id": publisher_2_id,
        },
    )
    book_3_id = book_table.insert(
        {
            "name": "Nineteen Eighty-Four",
            "pages": 3,
            "release_year": 1949,
            "author_id": author_3_id,
            "publisher_id": publisher_3_id,
        },
    )
    book_table.insert(
        {
            "name": "This book was not written",
            "pages": 4,
            "release_year": 2100,
            "author_id": author_3_id,
            "publisher_id": publisher_3_id,
        },
    )
    library_table: dataset.Table = db["library"]
    library_1_id = library_table.insert({"name": "New York Public Library", "address": "224 East 125th Street"})
    library_2_id = library_table.insert({"name": "California State Library", "address": "900 N Street"})

    book_inventory_table: dataset.Table = db["book_inventory"]
    book_inventory_table.insert_many(
        [
            {"book_id": book_2_id, "library_id": library_1_id, "amount": 15},
            {"book_id": book_3_id, "library_id": library_1_id, "amount": 40},
            {"book_id": book_1_id, "library_id": library_2_id, "amount": 25},
            {"book_id": book_2_id, "library_id": library_2_id, "amount": 30},
        ]
    )

    # 3) Select books
    books = book_table.find(release_year={"<": 1960}, order_by=["name", "pages"], _limit=10)
    for book in books:
        logger.info(f"Found books released before 1960: {book}")

    ids = [1960, 1961]
    # Works also with empty arrays:
    # ids = []
    placeholders = ", ".join(f":{i}" for i in range(len(ids)))
    results = db.query(
        f"SELECT id, name, author_id, publisher_id FROM book WHERE release_year IN ({placeholders})",
        {f"{i}": value for i, value in enumerate(ids)},
    )
    for book in results:
        logger.info(f"Found books released in 1960 or 1961: {book}")

    # 4) Update books
    # Assert before
    assert book_table.count(release_year={"<": 1960}) == 2
    # Do update
    rows = book_table.find(release_year={"<": 1960})
    updated = (row | dict(release_year=1970) for row in rows)
    book_table.upsert_many(updated, ["id"])
    # Alternatively with raw query
    db.query(
        "UPDATE book SET release_year=:target_year WHERE release_year < :year",
        {
            "year": 1960,
            "target_year": 1960,
        },
    )
    # Assert after
    assert book_table.count(release_year={"<": 1960}) == 0

    # 5) Delete books
    # Assert before
    assert book_table.count() == 4
    # Do remove
    book_table.delete(name="This book was not written")
    # Assert after
    assert book_table.count() == 3

    # 6) Get data from other tables
    for row in db.query(
        """
SELECT book.id, book.name, book.release_year, author_id, publisher_id,
a.name AS author_name, a.birth_year, p.name AS publisher_name, p.founded_year
FROM book
JOIN author a on book.author_id = a.id
JOIN publisher p on book.publisher_id = p.id
        """
    ):
        row_as_dict = dict(row)
        logger.info(f"Book, author and publisher information: {row_as_dict}")

    # 7) Join two tables and apply filter
    for row in db.query(
        """
SELECT book_inventory.library_id, book_inventory.book_id, book_inventory.amount,
b.name, b.release_year, a.name AS author_name, a.birth_year,
l.name AS library_name, l.address AS library_address
FROM book_inventory
JOIN book b on book_inventory.book_id = b.id
JOIN author a on b.author_id = a.id
JOIN library l on book_inventory.library_id = l.id
WHERE
    book_inventory.amount >= 25
    AND a.birth_year < 1910
        """
    ):
        logger.info(f"Book, author and publisher information: {row}")

    # 8) Run migration (verify and change table schema if necessary)
    assert len(book_table.columns) == 6
    book_table.insert({"name": "A test book", "pages": 1, "rating": 4.5})
    assert len(book_table.columns) == 7
    book_table.delete(name="A test book")
    assert len(book_table.columns) == 7

    # 9) Clear table
    assert book_table.count() == 3
    book_table.delete()
    assert book_table.count() == 0

    # print(db.tables)


if __name__ == "__main__":
    run_database_with_dataset_readme_example()
