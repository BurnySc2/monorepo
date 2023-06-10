from __future__ import annotations

import gzip
import lzma
import zipfile
from io import BytesIO
from pathlib import Path

from loguru import logger

from src.argparser import compress_files

# poetry run python -m pytest

PARENT_DIR = Path(__file__).parent
TXT_FILE = PARENT_DIR / "transcribed.txt"
SRT_FILE = PARENT_DIR / "transcribed.srt"

with TXT_FILE.open() as f:
    TXT_DATA = f.read()

with SRT_FILE.open() as f:
    SRT_DATA = f.read()


def compress_files_zipfile_stored(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_STORED, compresslevel=9) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def compress_files_zipfile_deflated(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def compress_files_zipfile_bzip(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_BZIP2, compresslevel=9) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def compress_files_zipfile_lzma(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_LZMA, compresslevel=9) as zip_file:
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


def test_compress_txt():
    txt_compression_results = {
        "implementation": helper_get_size(compress_files({"a": TXT_DATA})),
        "zipfile_stored": helper_get_size(compress_files_zipfile_stored({"a": TXT_DATA})),
        "zipfile_deflated": helper_get_size(compress_files_zipfile_deflated({"a": TXT_DATA})),
        "zipfile_bzip": helper_get_size(compress_files_zipfile_bzip({"a": TXT_DATA})),
        "zipfile_lzma": helper_get_size(compress_files_zipfile_lzma({"a": TXT_DATA})),
        "gzip": helper_get_size(compress_file_gzip(TXT_DATA)),
        "lzma": helper_get_size(compress_file_lzma(TXT_DATA)),
    }

    logger.info(txt_compression_results)
    # assert txt_compression_results["implementation"] <= min(txt_compression_results.values())


def test_compress_srt():
    srt_compression_results = {
        "implementation": helper_get_size(compress_files({"a": SRT_DATA})),
        "zipfile_stored": helper_get_size(compress_files_zipfile_stored({"a": SRT_DATA})),
        "zipfile_deflated": helper_get_size(compress_files_zipfile_deflated({"a": SRT_DATA})),
        "zipfile_bzip": helper_get_size(compress_files_zipfile_bzip({"a": SRT_DATA})),
        "zipfile_lzma": helper_get_size(compress_files_zipfile_lzma({"a": SRT_DATA})),
        "gzip": helper_get_size(compress_file_gzip(SRT_DATA)),
        "lzma": helper_get_size(compress_file_lzma(SRT_DATA)),
    }

    logger.info(srt_compression_results)
    # assert srt_compression_results["implementation"] <= min(srt_compression_results.values())
