from __future__ import annotations

import zipfile
from collections.abc import Iterable
from io import BytesIO
from pathlib import Path


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


def generate_txt_data(transcribed_data: list[tuple[float, float, str]]) -> str:
    data_list:list[str] = []
    for line in transcribed_data:
        data_list.append(f"{line[2]}\n")
    return "".join(data_list)


def compress_files(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def decompress_files(zip_file: BytesIO) -> dict[str, str]:
    decompressed = {}
    # pyrefly: ignore
    with zipfile.ZipFile(zip_file) as zip_file:
        # pyrefly: ignore
        for file_name in zip_file.namelist():
            # pyrefly: ignore
            with zip_file.open(file_name) as file:
                decompressed[file_name] = file.read().decode()
    return decompressed
