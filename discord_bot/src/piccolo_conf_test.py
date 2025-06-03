from pathlib import Path

from piccolo.engine.sqlite import SQLiteEngine

db_path = Path(__file__).parent / "temp.db"
DB = SQLiteEngine(path=str(db_path.absolute()))
