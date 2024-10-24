"""
Import all models from this file to ensure that they are registered with PonyORM.
"""
from __future__ import annotations

import zipfile
from io import BytesIO

from faster_whisper import format_timestamp  # pyre-fixme[21]


def generate_txt_data(transcribed_data: list[tuple[float, float, str]]) -> str:
    data_list = []
    for line in transcribed_data:
        data_list.append(f"{line[2]}\n")
    return "".join(data_list)


def generate_srt_data(transcribed_data: list[tuple[float, float, str]]) -> str:
    # def seconds_to_timestamp(seconds: float) -> str:
    #     minutes, seconds = divmod(seconds, 60)
    #     hours, minutes = divmod(minutes, 60)
    #     milliseconds = f"{seconds:.3f}".split(".")[1]
    #     return f"{hours:02}:{minutes:02}:{seconds:02},{milliseconds}"
    data_list = []
    for i, line in enumerate(transcribed_data, start=1):
        data_list.append(f"{i}\n")
        start = format_timestamp(line[0], always_include_hours=True, decimal_marker=",")
        end = format_timestamp(line[1], always_include_hours=True, decimal_marker=",")
        data_list.append(f"{start} --> {end}\n")
        data_list.append(f"{line[2]}\n\n")
    return "".join(data_list)


def compress_files(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def decompress_files(zip_file: BytesIO) -> dict[str, str]:
    decompressed = {}
    with zipfile.ZipFile(zip_file, mode="r") as zip_file:
        for file_name in zip_file.namelist():
            with zip_file.open(file_name, mode="r") as file:
                decompressed[file_name] = file.read().decode()
    return decompressed
