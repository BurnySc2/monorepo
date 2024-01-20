"""
SQLite help:
https://www.sqlitetutorial.net
https://www.tutorialspoint.com/sqlite/index.htm
https://docs.python.org/3/library/sqlite3.html

SQL tutorials:
https://sqlzoo.net/wiki/SQL_Tutorial

SQL quizzes and challenges
https://sqlbolt.com
https://pgexercises.com
https://www.sql-practice.com
https://mystery.knightlab.com
"""
import math
import sqlite3

from loguru import logger


def calc_distance(x0: float, y0: float, x1: float, y1: float) -> float:
    return math.dist((x0, y0), (x1, y1))


def test_database():
    # with sqlite3.connect("example.db") as db:
    with sqlite3.connect(":memory:") as db:
        # Instead of returning tuples, return dicts https://stackoverflow.com/a/55986968
        db.row_factory = sqlite3.Row

        # Add a custom function
        # https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.create_function
        db.create_function("dist", 4, calc_distance, deterministic=True)

        # Creates a new table "people" with 3 columns: text, real, integer
        # Fields marked with PRIMARY KEY are columns with unique values (?)
        db.execute(
            """
            CREATE TABLE IF NOT EXISTS people
            (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL CHECK(length(name) >= 3),
                age INTEGER NOT NULL CHECK(age >= 0),
                height REAL NOT NULL CHECK(height >= 0),
                x REAL NOT NULL,
                y REAL NOT NULL
            )
            """
        )

        # Insert via string
        db.execute("INSERT INTO people (name, age, height, x, y) VALUES ('Someone', 80, 1.60, 100, 100)")
        # Insert by tuple
        db.execute(
            "INSERT INTO people (name, age, height, x, y) VALUES (?, ?, ?, ?, ?)", ("Someone Else", 50, 1.65, 125, 75)
        )
        # Optional (name, age, height) if all columns are supplied
        # db.execute("INSERT INTO people VALUES (?, ?, ?)", ("Someone Else", 50, 1.65))

        friends = [
            ("Someone Else1", 40, 1.70, 80, 120),
            ("Someone Else2", 30, 1.75, 85, 125),
            ("Someone Else3", 20, 1.80, 90, 115),
            ("Someone Else4", 20, 1.85, 105, 150),
        ]
        # Insert many over iterable
        db.executemany("INSERT INTO people (name, age, height, x, y) VALUES (?, ?, ?, ?, ?)", friends)

        # Insert unique name again
        try:
            db.execute(
                "INSERT INTO people (name, age, height, x, y) VALUES (?, ?, ?, ?, ?)",
                ("Someone Else", 50, 1.65, 100, 100),
            )
        except sqlite3.IntegrityError:
            logger.info("Name already exists: Someone Else")

        # Delete an entry https://www.w3schools.com/sql/sql_delete.asp
        db.execute("DELETE FROM people WHERE age=40")

        # Update entries https://www.w3schools.com/sql/sql_update.asp
        db.execute("UPDATE people SET height=1.90, age=35 WHERE name='Someone Else'")

        # Insert a value if it doesnt exist, or replace if it exists
        db.execute("REPLACE INTO people (name, age, height, x, y) VALUES ('Someone Else5', 32, 2.01, 55, 55)")

        # Insert entries or update if it exists, 'upsert' https://www.sqlite.org/lang_UPSERT.html
        # Might not work on old sqlite3 versions
        # db.execute(
        #     "INSERT INTO people VALUES ('Someone Else', 35, 1.95) ON CONFLICT(name) DO UPDATE SET height=1.95, age=35"
        # )
        # db.execute(
        #     "INSERT INTO people VALUES ('Someone Else5', 32, 2.00)
        #     ON CONFLICT(name) DO UPDATE SET height=1.95, age=35"
        # )

        # Save database to hard drive, don't have to save when it is just in memory
        # db.commit()

        # SELECT: returns selected fields of the results, use * for all https://www.w3schools.com/sql/sql_select.asp
        # ORDER BY: Order by column 'age' and 'height' https://www.w3schools.com/sql/sql_orderby.asp
        # WHERE: Filters 'height >= 1.70' https://www.w3schools.com/sql/sql_where.asp
        logger.info("Example query")
        results: sqlite3.Cursor = db.execute(
            "SELECT id, name, age, height FROM people WHERE height>=1.70 and name!='Someone Else2' "
            "ORDER BY age ASC, height ASC",
        )
        for row in results:
            # Can also access values via row[0]
            row_as_dict = dict(row)
            logger.info(f"Row: {row_as_dict}")

        person = "Someone"
        max_distance = 50
        logger.info(f"Get all people in distance of {max_distance} of '{person}'")
        results: sqlite3.Cursor = db.execute(
            f"""
            SELECT id, name, dist(people.x, people.y, people2.x, people2.y) AS distance,
            SQRT(POW(people.x - people2.x, 2) + POW(people.y - people2.y, 2)) AS distance2
            FROM people
            JOIN (SELECT x, y FROM people WHERE name = '{person}' LIMIT 1) as people2
            WHERE name <> '{person}'
            AND distance < {max_distance}
            """,
        )
        for row in results:
            row_as_dict = dict(row)
            logger.info(f"Row: {row_as_dict}")

        # Exclude entries where the same age is listed twice
        # Here, age 20 is listed twice in the database, select all but those
        results = db.execute(
            """
            SELECT id, name, age, height
            FROM people
            GROUP BY age
            HAVING COUNT(age) == 1
            ORDER BY age ASC, height ASC
            """,
        )

        logger.info("Exclude query")
        for row in results:
            row_as_dict = dict(row)
            logger.info(f"Row: {row_as_dict}")

        # TODO: How to add or remove a column in existing database?
        # TODO: How to do migrations ideally? Migration table? How to set default values
        # TODO: How to join two database files?
        # TODO: More examples of "GROUP BY" and "HAVING"
        # TODO: Add datetime, strftime examples
        # TODO: Add interesting constraints for CHECK, e.g. check if snake_style or CamelCase or email format
        # TODO: Add LIKE examples
        # TODO: Add GLOB examples
        # TODO: Add aggregate example https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.create_aggregate
        # TODO: Add view examples (e.g. add column that adds 'age' based on today's date)

        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table in tables:
            table_name = table["name"]
            logger.info(f"Table: {table_name}")
            table_info = db.execute(f"pragma table_info({table_name})")
            for column_info in table_info:
                logger.info(dict(column_info))


if __name__ == "__main__":
    test_database()
