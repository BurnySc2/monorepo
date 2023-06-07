from __future__ import annotations

import asyncio
import sys
from io import BytesIO
from pathlib import Path
from typing import Generator

from faster_whisper import WhisperModel
from loguru import logger
from pony import orm
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


async def add_processing_jobs():
    """Based on settings from SECRETS.toml, uploading all matching mp3 files for transcribing."""
    with orm.db_session():
        uploaded_files: list[str] = list(orm.select(j.local_file for j in JobItem))

    if SECRETS.detect_language_before_queueing:
        model = WhisperModel(
            "large-v2",
            device="cpu",
            compute_type="int8",
            download_root="./whisper_models",
        )

    for folder in SECRETS.finder_folders_to_parse:
        folder_path = Path(folder)
        for path in recurse_path(folder_path, depth=10):
            if path.match(SECRETS.finder_ignore_glob_pattern):
                continue
            if not path.match(SECRETS.finder_add_glob_pattern):
                continue
            if str(path.absolute()) in uploaded_files:
                continue
            # TODO Skip if it already has a srt or txt transcription

            file_size_bytes = path.stat().st_size

            language_code = ""
            with path.open("rb") as f:
                file_data: BytesIO = BytesIO(f.read())
            if (
                SECRETS.detect_language_before_queueing
                and SECRETS.detect_language_before_queueing_min_size_bytes < file_size_bytes
            ):
                _, info = model.transcribe(file_data)
                language_code = info.language

            # Upload file to db
            logger.info(f"Uploading {file_size_bytes/2**20:.1f} mb {path.absolute()}")
            with orm.db_session():
                job_item = JobItem(
                    local_file=str(path.absolute()),
                    task=Task.Transcribe.name,
                    detected_language=language_code,
                    model_size=ModelSize.Small.name,
                    status=JobStatus.QUEUED.name,
                    input_file_size_bytes=file_size_bytes,
                )
                job_item.input_file_mp3 = Mp3File(job_item=job_item, mp3_data=file_data.getvalue())


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
    await asyncio.gather(
        add_processing_jobs(),
        download_processed_results(),
    )


if __name__ == "__main__":
    asyncio.run(main())
