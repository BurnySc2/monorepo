import os
from pathlib import Path

from loguru import logger


def create_file():
    example_file_path = Path(__file__).parent.parent.parent / 'data' / 'hello_world.txt'
    os.makedirs(example_file_path.parent, exist_ok=True)
    with example_file_path.open('w') as f:
        f.write('Hello world!\n')
    logger.info(f'Hello world file created in path {example_file_path}')
