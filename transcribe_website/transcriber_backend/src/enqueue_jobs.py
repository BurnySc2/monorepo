from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Generator

from loguru import logger
from pony import orm
from pony.orm.core import TransactionIntegrityError
from secrets_loader import SECRETS

sys.path.append(str(Path(__file__).parent.parent))
from db import JobItem, JobStatus, ModelSize, Mp3File, Task  # noqa: E402


def recurse_path(path: Path, depth: int = 1) -> Generator[Path, None, None]:
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


def add_processing_jobs():
    """Based on settings from SECRETS.toml, uploading all matching mp3 files for transcribing."""
    for folder in SECRETS.finder_folders_to_parse:
        folder_path = Path(folder)
        for path in recurse_path(folder_path, depth=10):
            if path.match(SECRETS.finder_ignore_glob_pattern):
                continue
            if not path.match(SECRETS.finder_add_glob_pattern):
                continue
            # TODO Skip if it already has a srt or txt transcribtion

            file_size_bytes = path.stat().st_size

            # Add db entry
            with orm.db_session():
                # Upload file to db
                logger.info(f"Uploading {file_size_bytes/2**20:.1f} mb {path.absolute()}")
                try:
                    job_item = JobItem(
                        local_file=str(path.absolute()),
                        task=Task.Transcribe.name,
                        model_size=ModelSize.Medium.name,
                        status=JobStatus.QUEUED.name,
                        input_file_size_bytes=file_size_bytes,
                    )
                    with path.open("rb") as f:
                        job_item.input_file_mp3 = Mp3File(job_item=job_item, mp3_data=f.read())
                except TransactionIntegrityError:
                    # Duplicate
                    continue
                # logger.info(f"Uploaded {path.absolute()}")


async def download_processed_results():
    """Download results from add_processing_jobs()."""
    # Check which files have already been processed and exported locally
    with orm.db_session():
        pass

    while 1:
        with orm.db_session():
            pass
        await asyncio.sleep(10)


async def main():
    asyncio.gather(
        add_processing_jobs(),
        download_processed_results(),
    )


if __name__ == "__main__":
    asyncio.run(main())
