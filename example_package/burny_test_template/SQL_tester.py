import random
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Type, Union

from loguru import logger
from lorem_text import lorem

random.seed(420)

# Source: https://github.com/smashew/NameDatabases
this_folder = Path(__file__).parent
with (this_folder / 'first_names.txt').open() as f:
    first_names = [i.strip() for i in f.readlines()]
with (this_folder / 'last_names.txt').open() as f:
    last_names = [i.strip() for i in f.readlines()]


def generate_name() -> str:
    first = random.randint(0, len(first_names))
    last = random.randint(0, len(last_names))
    first_name = first_names[first]
    last_name = last_names[last]
    return f'{first_name} {last_name}'


def generate_int() -> int:
    return random.randint(1000, 2_000_000)


def generate_float() -> float:
    return random.uniform(1000, 2_000_000)


def generate_year() -> int:
    return random.randint(1980, 1999)


def generate_bool() -> bool:
    return bool(random.randint(0, 1))


def generate_text() -> str:
    return lorem.words(2)


class SqlMetaclass:

    @classmethod
    def create_table(cls, db: sqlite3.Connection):
        """
        a = A()
        a.create_table(db)
        """
        database_column_types = {
            str: 'TEXT',
            int: 'INT',
            float: 'REAL',
            bool: 'BOOLEAN',
        }
        columns = [
            f'{column_name} {database_column_types[column_type]}'
            for column_name, column_type in cls.__annotations__.items()
        ]
        columns_joined = ', '.join(columns)
        logger.info(f'Creating table {cls.__name__} with columns ({columns_joined})')
        db.execute(f"""
        CREATE TABLE {cls.__name__} ({columns_joined})
        """)
        # db.commit()

    @classmethod
    def generate_data(cls, db: sqlite3.Connection, amount: int = 1):
        name_fields = {'artist_name'}
        rows: List[List[Union[float, bool, str]]] = []
        # TODO Overlapping items
        for _ in range(amount):
            row_entry: List[Union[float, bool, str]] = []
            for column_name, column_type in cls.__annotations__.items():
                if column_name in name_fields:
                    row_entry.append(generate_name())
                elif 'year' in column_name:
                    row_entry.append(generate_year())
                elif column_type == str:
                    row_entry.append(generate_text())
                elif column_type == int:
                    row_entry.append(generate_int())
                elif column_type == float:
                    row_entry.append(generate_float())
                elif column_type == bool:
                    row_entry.append(generate_bool())
                else:
                    raise TypeError(f'Column type must be one of: str, int, float, but was of type {column_type}')
            rows.append(row_entry)
        columns = [f'{column_name}' for column_name, column_type in cls.__annotations__.items()]
        columns_joined = ', '.join(columns)
        values_questionmarks = ','.join('?' for _ in columns)
        logger.info(f"Inserting the following rows into table '{cls.__name__}':")
        for row in rows:
            logger.info(f'{row}')
        db.executemany(
            f"""
        INSERT INTO {cls.__name__} ({columns_joined})
        VALUES ({values_questionmarks})
        """,
            rows,
        )

    def add_item_to_db(self, db: sqlite3.Connection):
        columns = [f'{column_name}' for column_name, column_type in self.__annotations__.items()]
        columns_joined = ', '.join(columns)
        values = [self.__dict__[column_name] for column_name in columns]
        values_joined = ', '.join(map(repr, values))
        table_name = self.__class__.__name__
        insert_string = f"""
        INSERT INTO {table_name} ({columns_joined})
        VALUES ({values_joined})
        """
        logger.info(f"Inserting: values '{values_joined}' into columns '{columns_joined}' into table '{table_name}'")
        db.execute(insert_string)

    # @classmethod
    # def print_table(cls, db: sqlite3.Connection):
    #     pass


# Define tables


@dataclass
class Song(SqlMetaclass):
    song_id: int
    song_name: str
    artist_id: int
    album_id: int
    genre: str
    song_length: int


@dataclass
class Album(SqlMetaclass):
    album_id: int
    album_name: str
    publish_year: int


@dataclass
class Artist(SqlMetaclass):
    artist_id: int
    artist_name: str
    birth_year: int
    verified: bool


if __name__ == '__main__':
    with sqlite3.connect(':memory:') as db:
        cls: Type[SqlMetaclass]
        for cls in [Song, Album, Artist]:
            # Create tables
            cls.create_table(db)
            # Generate data
            cls.generate_data(db, amount=3)

        # Add custom items to db
        Song(
            song_id=generate_int(),
            song_name=generate_name(),
            artist_id=generate_int(),
            album_id=1869690,
            genre=generate_text(),
            song_length=generate_int(),
        ).add_item_to_db(db)

        # Print data in database
        # TODO print data as table where each column has same width
        result = db.execute('SELECT * FROM Song')
        for i in result:
            # logger.info(Song(*i))
            pass

        # Run test query
        result = db.execute(
            """
        SELECT song_name, album_name, publish_year FROM Song JOIN Album
        ON Song.album_id = Album.album_id
        """,
        )
        result_list = list(map(list, result))

        # Compare result to expected
        expected = [['Jeannette Macha', 'doloribus unde', 1984]]
        assert result_list == expected, f'{result_list} != {expected}'
