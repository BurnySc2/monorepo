# Database
import sqlite3
from dataclasses import dataclass

from loguru import logger


def test_database_with_classes():
    @dataclass
    class Point:
        x: float
        y: float

        @staticmethod
        def serialize(p: "Point") -> bytes:
            return f"{p.x};{p.y}".encode("ascii")

        @staticmethod
        def deserialize(byte: bytes) -> "Point":
            x, y = list(map(float, byte.split(b";")))
            return Point(x, y)

    # Register the adapter / serializer
    sqlite3.register_adapter(Point, Point.serialize)

    # Register the converter
    sqlite3.register_converter("point", Point.deserialize)

    with sqlite3.connect(":memory:", detect_types=sqlite3.PARSE_DECLTYPES) as db:
        # Creates new table
        db.execute("CREATE TABLE IF NOT EXISTS points (name TEXT, p point)")

        points = [
            ["p1", Point(x=4.0, y=-3.2)],
            ["p2", Point(x=8.0, y=-6.4)],
        ]
        db.executemany("INSERT INTO points VALUES (?, ?)", points)
        for row in db.execute("SELECT * FROM points"):
            logger.info(f"Row: {row}")
