from pathlib import Path

from tinydb import Query, TinyDB


def test_database_with_tinydb():
    # Embedded pure-python dict based dictionary
    db_path = Path(__file__).parent.parent.parent / "data" / "db.json"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    db = TinyDB(db_path)
    User = Query()  # noqa: N806
    # Insert
    db.insert({"name": "John", "age": 22})
    # Find
    _result = db.search(User.name == "John")
    # Logical operators
    _result = db.search((User.name == "John") & (User.age < 30))


if __name__ == "__main__":
    test_database_with_tinydb()
