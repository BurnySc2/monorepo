"""
docker run --rm --name postgres \
    -e POSTGRES_USER=postgres \
    -e POSTGRES_PASSWORD=123 \
    -p 5432:5432 \
    -v postgres_data:/var/lib/postgresql/data \
    postgres:15-alpine
"""
# https://www.psycopg.org/psycopg3/docs/basic/usage.html
import psycopg

# Connect to an existing database
with psycopg.connect("postgresql://postgres:123@localhost:5432/postgres") as conn:  # noqa: SIM117
    # Open a cursor to perform database operations
    with conn.cursor() as cur:
        # Execute a command: this creates a new table
        cur.execute(
            # psycopg.errors.DuplicateTable: relation "test" already exists
            """
            CREATE TABLE test (
                id serial PRIMARY KEY,
                num integer,
                data text)
            """
        )

        # Pass data to fill a query placeholders and let Psycopg perform
        # the correct conversion (no SQL injections!)
        cur.execute("INSERT INTO test (num, data) VALUES (%s, %s)", (100, "abc'def"))

        # Query the database and obtain data as Python objects.
        cur.execute("SELECT * FROM test")
        cur.fetchone()
        # will return (1, 100, "abc'def")

        # You can use `cur.fetchmany()`, `cur.fetchall()` to return a list
        # of several records, or even iterate on the cursor
        for record in cur:
            print(record)

        # Make the changes to the database persistent
        conn.commit()
