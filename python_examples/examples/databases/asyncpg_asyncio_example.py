# Database
import asyncio
import time
from typing import List

import asyncpg
from loguru import logger

_docker_command = 'docker run -d --rm --name postgresql-container -p 54321:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=changeme postgres:9.6.23-alpine3.14'


async def test_asyncpg_database():
    # Connect to postgres server - doesn't work with memory or local file
    try:
        db: asyncpg.Connection = await asyncpg.connect(
            user='postgres',
            password='changeme',
            database='postgres',
            host='127.0.0.1',
            port=54321,
        )
    except ConnectionRefusedError:
        logger.error(f'Unable to connect to postgresql. Try starting it via docker command: {_docker_command}')
        return

    # Create table
    await db.execute('CREATE TABLE IF NOT EXISTS people (id SERIAL, name TEXT UNIQUE, age INTEGER, height REAL)')
    # Clear table
    await db.execute('DELETE FROM people')

    # Insert via string
    await db.execute("INSERT INTO people (name, age, height) VALUES ('Someone', 80, 1.60)")
    logger.info('Example query')
    results = await db.fetch('SELECT id, name, age, height FROM people')

    for row in results:
        row_as_dict = dict(row)
        logger.info(f'Row: {row_as_dict}')

    await db.close()


async def performance_test_asyncpg_database():
    # No clue what the difference between a connection and a pool is, but asyncio gather only works with pool
    try:
        db: asyncpg.Pool = await asyncpg.create_pool(
            user='postgres',
            password='changeme',
            database='postgres',
            host='127.0.0.1',
            port=54321,
        )
    except ConnectionRefusedError:
        logger.error(f'Unable to connect to postgresql. Try starting it via docker command: {_docker_command}')
        return
    # Create table
    await db.execute('CREATE TABLE IF NOT EXISTS people (id SERIAL, name TEXT UNIQUE, age INTEGER, height REAL)')
    # Clear table
    await db.execute('DELETE FROM people')

    t0 = time.perf_counter()
    tasks = []
    for i in range(1000):
        tasks.append(
            asyncio.create_task(
                db.execute(
                    'INSERT INTO people (name, age, height) VALUES ($1, $2, $3)',
                    f'Someone{i}',
                    i,
                    0.0,
                ),
            ),
        )
    await asyncio.gather(*tasks)
    t1 = time.perf_counter()
    # 0.2 - 1.8 seconds for 1000 entries - any way to make it faster without using executemany?
    logger.info(f'Required time: {t1-t0:.3f} seconds')

    logger.info('Example query')
    results: List[asyncpg.Record] = await db.fetch('SELECT id, name, age, height FROM people ORDER BY age LIMIT 5')

    for row in results:
        row_as_dict = dict(row)
        logger.info(f'Row: {row_as_dict}')

    await db.close()


async def main():
    # await test_asyncpg_database()
    await performance_test_asyncpg_database()


if __name__ == '__main__':
    asyncio.run(main())
