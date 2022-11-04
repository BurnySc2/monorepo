from pathlib import Path
from typing import Iterable


def convert_string_to_path(multi_line_string: str) -> Iterable[Path]:
    """
    Convert a given list of paths as single string

        /root/some/file
        /root/some/other/file

    to an iterator of Path
    """
    for line in multi_line_string.strip().split('\n'):
        yield Path(line)


def recurse_path(path: Path, depth: int = 0) -> Iterable[Path]:
    """
    Go through a given path recursively and return file paths

    If depth == 0: only allow file path
    If depth == 1: if given a folder, return containing file paths
    Depth > 1 allow recursively to go through folders up to a given depth
    """
    if path.is_file():
        yield path
    elif path.is_dir() and depth > 0:
        for subfile_path in sorted(path.iterdir()):
            yield from recurse_path(subfile_path, depth=depth - 1)
