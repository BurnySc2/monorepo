from __future__ import annotations

import asyncio
import sys
from io import BytesIO
from pathlib import Path
from typing import Generator

from faster_whisper import WhisperModel  # pyre-fixme[21]
from loguru import logger
from pony import orm  # pyre-fixme[21]

sys.path.append(str(Path(__file__).parent.parent))
from src.models.db import (  # noqa: E402
    JobStatus,
    ModelSize,
    Task,
    TelegramMessage,
    TranscriptionJob,
    TranscriptionMp3File,
)
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

SECRETS = SECRETS_FULL.Transcriber


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
        uploaded_files: list[str] = list(orm.select(j.local_file for j in TranscriptionJob))

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
            relative_file_path = path.relative_to(folder_path)
            relative_file_path_str = str(relative_file_path)
            if relative_file_path_str in uploaded_files:
                with orm.db_session():
                    # Link telegram message to transcription job
                    related_message: TelegramMessage | None = TelegramMessage.get(
                        downloaded_file_path=relative_file_path_str
                    )
                    transcription_job = TranscriptionJob.get(local_file=relative_file_path_str)
                    if related_message is not None and transcription_job is not None:
                        related_message.linked_transcription = transcription_job
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
                transcription_job = TranscriptionJob(
                    local_file=relative_file_path_str,
                    task=Task.Transcribe.name,
                    forced_language=language_code,
                    model_size=ModelSize.Small.name,
                    status=JobStatus.QUEUED.name,
                    input_file_size_bytes=file_size_bytes,
                )
                transcription_job.input_file_mp3 = TranscriptionMp3File(
                    job_item=transcription_job, mp3_data=file_data.getvalue()
                )
                # Link message to transcription job if it exists
                related_message: TelegramMessage | None = TelegramMessage.get(
                    downloaded_file_path=relative_file_path_str
                )
                if related_message is not None:
                    related_message.linked_transcription = transcription_job
    logger.warning("Done uploading files!")


async def main():
    await add_processing_jobs()


if __name__ == "__main__":
    asyncio.run(main())
