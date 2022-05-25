import sqlite3

from loguru import logger


def test_database():
    # with sqlite3.connect("example.db") as db:
    with sqlite3.connect(':memory:') as db:
        # Instead of returning tuples, return dicts https://stackoverflow.com/a/55986968
        db.row_factory = sqlite3.Row

        # Creates a new table "people" with 3 columns: text, real, integer
        # Fields marked with PRIMARY KEY are columns with unique values (?)
        db.execute(
            'CREATE TABLE IF NOT EXISTS people (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(30) UNIQUE, age INTEGER, height REAL)',
        )

        # Insert via string
        db.execute("INSERT INTO people (name, age, height) VALUES ('Someone', 80, 1.60)")
        # Insert by tuple
        db.execute('INSERT INTO people (name, age, height) VALUES (?, ?, ?)', ('Someone Else', 50, 1.65))
        # Optional (name, age, height) if all columns are supplied
        # db.execute("INSERT INTO people VALUES (?, ?, ?)", ("Someone Else", 50, 1.65))

        friends = [
            ('Someone Else1', 40, 1.70),
            ('Someone Else2', 30, 1.75),
            ('Someone Else3', 20, 1.80),
            ('Someone Else4', 20, 1.85),
        ]
        # Insert many over iterable
        db.executemany('INSERT INTO people (name, age, height) VALUES (?, ?, ?)', friends)

        # Insert unique name again
        try:
            db.execute('INSERT INTO people (name, age, height) VALUES (?, ?, ?)', ('Someone Else', 50, 1.65))
        except sqlite3.IntegrityError:
            logger.info('Name already exists: Someone Else')

        # Delete an entry https://www.w3schools.com/sql/sql_delete.asp
        db.execute('DELETE FROM people WHERE age=40')

        # Update entries https://www.w3schools.com/sql/sql_update.asp
        db.execute("UPDATE people SET height=1.90, age=35 WHERE name='Someone Else'")

        # Insert a value if it doesnt exist, or replace if it exists
        db.execute("REPLACE INTO people (name, age, height) VALUES ('Someone Else5', 32, 2.01)")

        # Insert entries or update if it exists, 'upsert' https://www.sqlite.org/lang_UPSERT.html
        # Might not work on old sqlite3 versions
        # db.execute(
        #     "INSERT INTO people VALUES ('Someone Else', 35, 1.95) ON CONFLICT(name) DO UPDATE SET height=1.95, age=35"
        # )
        # db.execute(
        #     "INSERT INTO people VALUES ('Someone Else5', 32, 2.00) ON CONFLICT(name) DO UPDATE SET height=1.95, age=35"
        # )

        # Save database to hard drive, don't have to save when it is just in memory
        # db.commit()

        # SELECT: returns selected fields of the results, use * for all https://www.w3schools.com/sql/sql_select.asp
        # ORDER BY: Order by column 'age' and 'height' https://www.w3schools.com/sql/sql_orderby.asp
        # WHERE: Filters 'height >= 1.70' https://www.w3schools.com/sql/sql_where.asp
        logger.info('Example query')
        results: sqlite3.Cursor = db.execute(
            "SELECT id, name, age, height FROM people WHERE height>=1.70 and name!='Someone Else2' ORDER BY age ASC, height ASC",
        )
        for row in results:
            # Can also access values via row[0]
            row_as_dict = dict(row)
            logger.info(f'Row: {row_as_dict}')

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

        logger.info('Exclude query')
        for row in results:
            row_as_dict = dict(row)
            logger.info(f'Row: {row_as_dict}')

        # TODO: How to add or remove a column in existing database?
        # TODO: How to join two databases?

        tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'")
        for table in tables:
            table_name = table['name']
            logger.info(f'Table: {table_name}')
            table_info = db.execute(f'pragma table_info({table_name})')
            for column_info in table_info:
                logger.info(dict(column_info))


if __name__ == '__main__':
    test_database()
