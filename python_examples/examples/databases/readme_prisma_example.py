"""
Assume database is empty. Insert only works when constraints are met.
"""
# Run commands from python_examples folder

# Update database tables
# poetry run prisma db push --schema examples/databases/prisma/schema.prisma

# Update schema from db
# poetry run prisma db pull --schema examples/databases/prisma/schema.prisma

# Update types (will be updated in .venv site-packages folder)
# poetry run prisma generate --watch --schema examples/databases/prisma/schema.prisma


import asyncio

from prisma import Prisma
from prisma.models import Author


async def main() -> None:
    db = Prisma(auto_register=True, log_queries=True)
    db.connect()

    # 1) Create tables
    # Tables already created by the "push" command

    # 2) Fill tables
    assert db.book.count(where={}) == 0

    # Book 1
    book1 = db.book.create(
        {
            "name": "The Lord of the Rings",
            "pages": 1,
            "release_year": 1954,
            "author": {
                "create": {
                    "name": "J. R. R. Tolkien",
                    "birth_year": 1892,
                }
            },
            "publisher": {
                "create": {
                    "name": "Hoffmann und Campe",
                    "founded_year": 1781,
                }
            },
        },
    )

    # Book 2
    book2 = db.book.create(
        {
            "name": "To kill a Mockingbird",
            "pages": 2,
            "release_year": 1960,
            "author": {
                "create": {
                    "name": "Harper Lee",
                    "birth_year": 1926,
                }
            },
            "publisher": {
                "create": {
                    "name": "Aufbau-Verlag",
                    "founded_year": 1781,
                }
            },
        },
    )

    # Book 3
    book3 = db.book.create(
        {
            "name": "Nineteen Eighty-Four",
            "pages": 3,
            "release_year": 1949,
            "author": {
                "create": {
                    "name": "George Orwell",
                    "birth_year": 1903,
                }
            },
            "publisher": {
                "create": {
                    "name": "Heyne Verlag",
                    "founded_year": 1934,
                }
            },
        },
    )

    # Book 4
    book4 = db.book.create(
        {
            "name": "This book was not written",
            "pages": 4,
            "release_year": 2100,
            # Author already exists, have to use author_id
            "author": {"connect": {"id": book3.author_id}},
            # Publisher already exists, have to use publisher_id
            "publisher": {"connect": {"id": book3.publisher_id}},
            # Alternative syntax if no create/connect is used:
            # "author_id": book3.author_id,
            # "publisher_id": book3.publisher_id,
        },
    )

    # Create book inventories
    library_inventory_1 = db.bookinventory.create(
        {
            "book": {"connect": {"id": book3.id}},
            "library": {
                "create": {
                    "name": "New York Public Library",
                    "address": "224 East 125th Street",
                }
            },
            "amount": 40,
        },
    )
    library_inventory_2 = db.bookinventory.create(
        {
            "book_id": book2.id,
            # Library1 already created by library_inventory_1
            "library_id": library_inventory_1.library_id,
            "amount": 15,
        },
    )
    library_inventory_3 = db.bookinventory.create(
        {
            "book": {"connect": {"id": book1.id}},
            "library": {
                "create": {
                    "name": "California State Library",
                    "address": "900 N Street",
                }
            },
            "amount": 25,
        },
    )
    library_inventory_4 = db.bookinventory.create(
        {
            "book_id": book2.id,
            # Library2 already created by library_inventory_3
            "library_id": library_inventory_3.library_id,
            "amount": 30,
        },
    )

    # 3) Select books
    books = db.book.find_many(
        where={
            "release_year": {
                "lt": 1960,
            },
        },
        include={
            # This only fetches the author
            # "author": True,
            # This fetches all the books by the book author
            "author": {
                "include": {
                    "books": True,
                },
            },
            "publisher": True,
        },
        order=[
            {
                "name": "desc",
            },
            {
                "pages": "asc",
            },
        ],
        take=10,
    )

    # 4) Update books
    assert db.book.count(where={"release_year": {"lt": 1960}}) == 2
    db.book.update_many(where={}, data={"release_year": 1970})
    assert db.book.count(where={"release_year": {"lt": 1960}}) == 0

    # 5) Delete books
    assert db.book.count(where={}) == 4
    db.book.delete_many(where={"name": "This book was not written"})
    assert db.book.count(where={}) == 3

    # 6) Get data from other tables
    books = db.book.find_many()
    assert len(books) == 3
    assert all(book.author is None and book.publisher is None for book in books)

    # Relation only filled if we use "include"
    books = db.book.find_many(include={"author": True, "publisher": True})
    assert len(books) == 3
    assert all(book.author is not None and book.publisher is not None for book in books)

    # 7) Join two tables and apply filter on relational fields
    book_inventories = db.bookinventory.find_many(
        where={
            # Filter where book amount >=25
            "amount": {"gte": 25},
            # Filter where the book author birth_year is less than 1910
            "book": {"author": {"birth_year": {"lt": 1910}}},
        },
        include={"book": {"include": {"author": True}}, "library": True},
    )
    assert len(book_inventories) == 2

    # 8) Alter table: Managed by CLI

    # 9) Delete all books

    # Requires on each model that has required Book field:
    # onDelete: Cascade
    assert db.book.count(where={}) == 3
    db.book.delete_many()
    assert db.book.count(where={}) == 0

    db.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
