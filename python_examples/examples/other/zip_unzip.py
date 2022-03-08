import io
from pathlib import Path
from typing import Iterable
from zipfile import ZIP_DEFLATED, ZipFile

from burny_common.path_manipulation import recurse_path


def zip_multiple_files(file_paths: Iterable[Path]) -> bytes:
    zip_buffer = io.BytesIO()
    with ZipFile(zip_buffer, 'w', ZIP_DEFLATED, False) as zipfile_handler:
        for file_path in file_paths:
            file_name = file_path.name
            with file_path.open() as f:
                zipfile_handler.writestr(file_name, f.read())

    zip_as_data: bytes = zip_buffer.getvalue()
    return zip_as_data


def unzip_multiple_files(data: bytes, target_folder: Path) -> None:
    with ZipFile(io.BytesIO(data)) as zip_file:
        zip_file.extractall(target_folder)


def main():
    this_folder_path = Path(__file__).parent
    temp_path = this_folder_path / 'temp'
    zipped = zip_multiple_files(recurse_path(
        this_folder_path,
        depth=1,
    ))
    unzip_multiple_files(zipped, temp_path)


if __name__ == '__main__':
    main()
