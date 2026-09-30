from __future__ import annotations

import gzip
import lzma
import zipfile
from io import BytesIO
from pathlib import Path

from loguru import logger

import pytest
from hypothesis import given, settings

import hypothesis.strategies as st

from src.helper import compress_files, decompress_files

# uv run python -m pytest

PARENT_DIR = Path(__file__).parent
TXT_FILE = PARENT_DIR / "transcribed.txt"
SRT_FILE = PARENT_DIR / "transcribed.srt"

with TXT_FILE.open() as f:
    TXT_DATA = f.read()

with SRT_FILE.open() as f:
    SRT_DATA = f.read()

COMPRESSION_LEVEL = 9
SIZE_TOLERANCE_BYTES = 50


def compress_files_zipfile(files: dict[str, str], compression: int = zipfile.ZIP_DEFLATED) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=compression, compresslevel=COMPRESSION_LEVEL) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def compress_file_gzip(data: str) -> bytes:
    return gzip.compress(data.encode())


def compress_file_lzma(data: str) -> bytes:
    return lzma.compress(data.encode())


def helper_get_size(data: bytes | BytesIO) -> int:
    if isinstance(data, bytes):
        return len(data)
    if isinstance(data, BytesIO):
        return len(data.getvalue())
    raise TypeError(f"unsupported type: {type(data)!r}")


@pytest.mark.parametrize("data", [TXT_DATA, SRT_DATA], ids=["txt", "srt"])
def test_compress(data: str):
    compression_results = {
        "implementation": helper_get_size(compress_files({"a": data})),
        "zipfile_stored": helper_get_size(compress_files_zipfile({"a": data}, compression=zipfile.ZIP_STORED)),
        "zipfile_deflated": helper_get_size(compress_files_zipfile({"a": data}, compression=zipfile.ZIP_DEFLATED)),
        "zipfile_bzip": helper_get_size(compress_files_zipfile({"a": data}, compression=zipfile.ZIP_BZIP2)),
        "zipfile_lzma": helper_get_size(compress_files_zipfile({"a": data}, compression=zipfile.ZIP_LZMA)),
        "gzip": helper_get_size(compress_file_gzip(data)),
        "lzma": helper_get_size(compress_file_lzma(data)),
    }

    logger.info(compression_results)
    # assert compression_results["implementation"] <= min(compression_results.values())


@pytest.mark.parametrize(
    "files",
    [
        {"transcribed.txt": TXT_DATA},
        {"transcribed.srt": SRT_DATA},
        {"transcribed.txt": TXT_DATA, "transcribed.srt": SRT_DATA},
        {},
        {"empty.txt": ""},
    ],
    ids=["txt", "srt", "multi", "empty_dict", "empty_file"],
)
def test_roundtrip(files: dict[str, str]):
    assert decompress_files(compress_files(files)) == files


def test_roundtrip_determinism():
    files = {"transcribed.txt": TXT_DATA, "transcribed.srt": SRT_DATA}
    first = compress_files(files)
    second = compress_files(files)
    # Zip headers embed timestamps, so compare size and roundtrip content instead of raw bytes.
    assert helper_get_size(first) == helper_get_size(second)
    assert decompress_files(first) == files
    assert decompress_files(second) == files


@pytest.mark.parametrize("data", [TXT_DATA, SRT_DATA], ids=["txt", "srt"])
def test_deflated_smaller_than_stored(data: str):
    stored = helper_get_size(compress_files_zipfile({"a": data}, compression=zipfile.ZIP_STORED))
    deflated = helper_get_size(compress_files({"a": data}))
    assert deflated + SIZE_TOLERANCE_BYTES < stored


@given(
    files=st.dictionaries(
        keys=st.text(alphabet=st.characters(blacklist_characters="\x00"), min_size=1, max_size=20),
        values=st.text(max_size=1000),
        max_size=3,
    ),
)
@settings(max_examples=20, deadline=None)
def test_roundtrip_hypothesis(files: dict[str, str]):
    assert decompress_files(compress_files(files)) == files


@given(
    files=st.dictionaries(
        keys=st.text(alphabet=st.characters(blacklist_characters="\x00"), min_size=1, max_size=20),
        values=st.text(max_size=1000),
        max_size=3,
    ),
)
@settings(max_examples=20, deadline=None)
def test_determinism_hypothesis(files: dict[str, str]):
    first = compress_files(files)
    second = compress_files(files)
    assert helper_get_size(first) == helper_get_size(second)
    assert decompress_files(first) == files
    assert decompress_files(second) == files
