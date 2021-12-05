import subprocess
from pathlib import Path

from loguru import logger

IGNORE_FILES = {'__init__', 'main', 'run', 'write_tests'}
IGNORE_STARTS_WITH_FILES = {'test_'}


def write_tests_for_folder(folder: Path):
    for file in folder.iterdir():
        if file.is_dir():
            write_tests_for_folder(file)
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

        command: list[str] = ['poetry', 'run', 'hypothesis', 'write', file.stem]
        process = subprocess.Popen(command, cwd=folder, stdout=subprocess.PIPE)
        out = process.stdout.read().decode()
        with target_test_file.open('w') as f:
            logger.info(f'Generating test file: {target_test_file.__str__()}')
            f.write(out)


def main():
    write_tests_for_folder(Path('.'))


if __name__ == '__main__':
    main()
