import os
from pathlib import Path
from typing import Set

file: Path
size_already_exists: Set[int] = set()
for file in pg`./**.*`:
    size = file.stat().st_size
    if file.is_file() and size in size_already_exists:
        print(f"Removing file '{file}'")
        os.remove(file)
    size_already_exists.add(size)
