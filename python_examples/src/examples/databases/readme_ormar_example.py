import asyncio
from pathlib import Path

import databases
import ormar
import sqlalchemy
from loguru import logger

db_path = Path(__file__).parent / "temp.db"
DATABASE_URL = f"sqlite:///{db_path.absolute()}"
base_ormar_config = ormar.OrmarConfig(
    database=databases.Database(DATABASE_URL),
    metadata=sqlalchemy.MetaData(),
    engine=sqlalchemy.create_engine(DATABASE_URL),
)


class Author(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="author")

    id: int = ormar.Integer(primary_key=True)
    name = ormar.Text()
    birth_year = ormar.Integer()


class Publisher(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="publisher")

    id: int = ormar.Integer(primary_key=True)
    name = ormar.Text()
    founded_year = ormar.Integer()


class Book(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="book")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.Text()
    pages = ormar.Integer()
    release_year = ormar.Integer()
    publisher: Publisher | None = ormar.ForeignKey(Publisher)
    author: Author | None = ormar.ForeignKey(Author)


class Library(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="library")

    id: int = ormar.Integer(primary_key=True)
    name: str = ormar.Text()
    address: str = ormar.Text()


class BookInventory(ormar.Model):
    ormar_config = base_ormar_config.copy(tablename="book_inventory")

    id: int = ormar.Integer(primary_key=True)
    book: Book | None = ormar.ForeignKey(Book)
    library: Library | None = ormar.ForeignKey(Library)
    amount: int = ormar.Integer()


async def run_database_with_ormar():
    # 1) Create tables
    base_ormar_config.metadata.create_all(base_ormar_config.engine)
    # base_ormar_config.metadata.drop_all(base_ormar_config.engine)

    # 2) Fill tables
    author_1 = await Author(name="J. R. R. Tolkien", birth_year=1892).save()
    author_2 = await Author(name="Harper Lee", birth_year=1926).save()
    author_3 = await Author(name="George Orwell", birth_year=1903).save()

    publisher_1 = await Publisher(name="Aufbau-Verlag", founded_year=1945).save()
    publisher_2 = await Publisher(name="Hoffmann und Campe", founded_year=1781).save()
    publisher_3 = await Publisher(name="Heyne Verlag", founded_year=1934).save()

    book_1 = await Book(
        name="The Lord of the Rings",
        pages=1,
        release_year=1954,
        author=author_1.id,
        publisher=publisher_2.id,
    ).save()
    book_2 = await Book(
        name="To kill a Mockingbird",
        pages=2,
        release_year=1960,
        author=author_2.id,
        publisher=publisher_1.id,
    ).save()
    book_3 = await Book(
        name="Nineteen Eighty-Four",
        pages=3,
        release_year=1949,
        author=author_3.id,
        publisher=publisher_3.id,
    ).save()
    _book_4 = await Book(
        name="This book was not written",
        pages=4,
        release_year=2100,
        author=author_3.id,
        publisher=publisher_3.id,
    ).save()

    library_1 = await Library(name="New York Public Library", address="224 East 125th Street").save()
    await BookInventory.objects.bulk_create(
        [
            BookInventory(book=book_3, library=library_1, amount=40),
            BookInventory(book=book_2, library=library_1, amount=15),
        ]
    )

    library_2 = await Library(name="California State Library", address="900 N Street").save()
    await BookInventory.objects.bulk_create(
        [
            BookInventory(book=book_1, library=library_2, amount=25),
            BookInventory(book=book_2, library=library_2, amount=30),
        ]
    )

    # 3) Select books
    books = await Book.objects.filter(release_year__lt=1960).order_by(["name", "-pages"]).all()
    # temp = await base_ormar_config.database.fetch_all("SELECT * FROM book")
    for book in books:
        logger.info(f"Found books released before 1960: {book}")


if __name__ == "__main__":
    try:
        asyncio.run(run_database_with_ormar())
    finally:
        db_path.unlink(missing_ok=True)
