import subprocess
from pathlib import Path
from typing import List

from loguru import logger

IGNORE_FILES = {'__init__', 'main', 'run', 'write_tests'}
IGNORE_FOLDERS = {'node_modules', '.venv'}
IGNORE_STARTS_WITH_FILES = {'test_', 'test-'}


def write_tests_for_folder(rootdir: Path, folder: Path):
    for file in folder.iterdir():
        if file.is_dir() and file.name in IGNORE_FOLDERS:
            continue
        if file.is_dir():
            write_tests_for_folder(rootdir, file)
            continue

        if file.suffix != '.py':
            continue
        if any(file.stem.startswith(i) for i in IGNORE_STARTS_WITH_FILES):
            continue
        if file.stem in IGNORE_FILES:
            continue

        target_test_file_name = f'test_{file.name}'
        target_test_file = folder / target_test_file_name
        if target_test_file.is_file():
            continue

        logger.info(f'Generating test file: {target_test_file.__str__()}')
        python_import_file_path = file.relative_to(rootdir).__str__().replace('/', '.')[:-3]
        command: List[str] = ['poetry', 'run', 'hypothesis', 'write', python_import_file_path]
        with subprocess.Popen(command, cwd=rootdir, stdout=subprocess.PIPE) as process:
            out = process.stdout
            if out is not None:
                data = out.read().decode()
                with target_test_file.open('w') as f:
                    f.write(data)


def main():
    write_tests_for_folder(Path('.'), Path('.'))


if __name__ == '__main__':
    main()
