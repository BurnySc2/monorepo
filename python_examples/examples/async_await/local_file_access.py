from __future__ import annotations

import asyncio
import random
from pathlib import Path
from string import printable

import aiofiles
from burny_common.measure_time import time_this  # pyre-fixme[21]

FILES_AMOUNT = 100
FILE_SIZE_IN_KB = 50

CURRENT_FOLDER_PATH = Path(__file__).parent


def write_files() -> list[Path]:
    created_files = []
    for index in range(FILES_AMOUNT):
        new_path = CURRENT_FOLDER_PATH / f"FILE_ACCESS_TEST_{index}"
        with new_path.open("w") as f:
            random_text = random.choices(printable, k=FILE_SIZE_IN_KB * 2**10)
            f.write("".join(random_text))
        created_files.append(new_path)
    return created_files


def read_sync(files: list[Path]) -> list[str]:
    read_data = []
    for file in files:
        with file.open() as f:
            read_data.append(f.read())
    return read_data


async def read_async_single_file(file: Path) -> str:
    async with aiofiles.open(file, "r") as f:
        return await f.read()


async def read_async(files: list[Path]) -> list[str]:
    tasks = []
    for file in files:
        tasks.append(asyncio.create_task(read_async_single_file(file)))
    read_data = []

    # results = await asyncio.gather(*tasks)
    # for result in results:
    #     read_data.append(result)

    for future in asyncio.as_completed(tasks):
        read_data.append(await future)
    return read_data


def delete_files(files: list[Path]):
    for file in files:
        file.unlink()


async def main():
    with time_this("Create files"):
        created_files = write_files()
    with time_this("Read files sync"):
        read_sync(created_files)
    with time_this("Read files async"):
        await read_async(created_files)
    with time_this("Delete files"):
        delete_files(created_files)


if __name__ == "__main__":
    asyncio.run(main())
