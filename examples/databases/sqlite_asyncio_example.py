# Database
import asyncio
import sqlite3
import time
from pathlib import Path

from databases import Database
from loguru import logger


async def test_asyncio_database():
    db_path = Path(__file__).parent.parent.parent / "data" / "sqlite_asyncio_example.db"
    async with Database(f'sqlite:///{db_path.absolute()}') as db:
        # Create table
        await db.execute(
            "CREATE TABLE IF NOT EXISTS people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, age INTEGER, height REAL)"
        )
        # Clear table
        await db.execute("DELETE FROM people")

        # Insert via string
        await db.execute("INSERT INTO people (name, age, height) VALUES ('Someone', 80, 1.60)")
        # Insert by dict values
        await db.execute(
            "INSERT INTO people (name, age, height) VALUES (:name, :age, :height)",
            values={
                "name": "Someone Else",
                "age": 50,
                "height": 1.65,
            }
        )

        # Insert multiple via list of dict
        friends = [
            dict(name="Someone Else1", age=40, height=1.70),
            dict(name="Someone Else2", age=30, height=1.75),
            dict(name="Someone Else3", age=20, height=1.80),
            dict(name="Someone Else4", age=20, height=1.85),
        ]
        # Insert many over iterable
        await db.execute_many("INSERT INTO people (name, age, height) VALUES (:name, :age, :height)", friends)

        # Insert unique name again - Error, already exists
        try:
            await db.execute(
                "INSERT INTO people (name, age, height) VALUES (:name, :age, :height)",
                dict(name="Someone Else", age=50, height=1.65)
            )
            assert False, "IntegrityError should've been raised"
        except sqlite3.IntegrityError:
            logger.info("Name already exists: Someone Else")

        # Delete an entry https://www.w3schools.com/sql/sql_delete.asp
        await db.execute("DELETE FROM people WHERE age=40")

        # Update entries https://www.w3schools.com/sql/sql_update.asp
        await db.execute("UPDATE people SET height=1.90, age=35 WHERE name='Someone Else'")

        # Insert a value if it doesnt exist, or replace if it exists
        await db.execute("REPLACE INTO people (name, age, height) VALUES ('Someone Else5', 32, 2.01)")

        # SELECT: returns selected fields of the results, use * for all https://www.w3schools.com/sql/sql_select.asp
        # ORDER BY: Order by column 'age' and 'height' https://www.w3schools.com/sql/sql_orderby.asp
        # WHERE: Filters 'height >= 1.70' https://www.w3schools.com/sql/sql_where.asp
        logger.info("Example query")
        results = await db.fetch_all(
            "SELECT id, name, age, height FROM people WHERE height>=1.70 and name != 'Someone Else2' ORDER BY age ASC, height ASC"
        )
        for row in results:
            logger.info(f"Row: {row}")

        # Exclude entries where the same age is listed twice
        # Here, age 20 is listed twice in the database, select all but those
        logger.info("Exclude query")
        results = await db.fetch_all(
            """
            SELECT id, name, age, height
            FROM people
            GROUP BY age
            HAVING COUNT(age) == 1
            ORDER BY age ASC, height ASC
            """
        )
        for row in results:
            row_as_dict = dict(row)
            logger.info(f"Row: {row_as_dict}")

        # Entry does not exist
        result = await db.fetch_one("SELECT name FROM people WHERE age==999")
        assert result is None


async def performance_test_asyncio_database():
    db_path = Path(__file__).parent.parent.parent / "data" / "sqlite_asyncio_example.db"
    async with Database(f'sqlite:///{db_path.absolute()}') as db:
        # Create table
        await db.execute(
            "CREATE TABLE IF NOT EXISTS people (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE, age INTEGER, height REAL)"
        )
        # Clear table
        await db.execute("DELETE FROM people")

        t0 = time.perf_counter()
        tasks = []
        for i in range(1000):
            tasks.append(
                asyncio.create_task(
                    db.execute(
                        "INSERT INTO people (name, age, height) VALUES (:name, :age, :height)",
                        values={
                            "name": f"Someone{i}",
                            "age": i,
                            "height": "0.0",
                        }
                    )
                )
            )
        await asyncio.gather(*tasks)
        t1 = time.perf_counter()
        # 6.7 seconds for 1000 entries - any way to make it faster without using executemany?
        logger.info(f"Required time: {t1-t0:.3f} seconds")


async def main():
    await test_asyncio_database()
    # await performance_test_asyncio_database()


if __name__ == '__main__':
    asyncio.run(main())
