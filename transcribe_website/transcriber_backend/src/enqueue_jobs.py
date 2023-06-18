from __future__ import annotations

import asyncio
import sys
import time
from io import BytesIO
from pathlib import Path
from typing import Generator

import humanize
from faster_whisper import WhisperModel  # pyre-fixme[21]
from loguru import logger
from pony import orm  # pyre-fixme[21]

from src.models.db import (  # noqa: E402
    JobStatus,
    ModelSize,
    Status,
    Task,
    TelegramMessage,
    TranscriptionJob,
    TranscriptionMp3File,
)
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

# Exclude debug logging messages
logger.remove()
logger.add(sys.stderr, level="INFO")

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


async def add_from_file_system():
    """Based on settings from SECRETS.toml, uploading all matching mp3 files for transcribing.
    Does not link to telegam messages.
    """
    with orm.db_session():
        uploaded_files: list[str] = set(orm.select(j.local_file for j in TranscriptionJob))

    if SECRETS.detect_language_before_queueing:
        model = WhisperModel(
            "large-v2",
            device="cpu",
            compute_type="int8",
            download_root="./whisper_models",
        )

    # TODO Loop over all files from telegram db instead
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
            logger.info(f"Uploading {humanize.naturalsize(file_size_bytes)} {path.absolute()}")
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
            uploaded_files.add(relative_file_path_str)
            if SECRETS.finder_delete_after_upload:
                path.unlink()
    logger.warning("Done uploading files!")


async def add_from_telegram_message():
    """Based on settings from SECRETS.toml, uploading all matching mp3 files for transcribing.
    Does link to telegram message"""
    with orm.db_session():
        uploaded_files: set[str] = set(orm.select(j.local_file for j in TranscriptionJob))

    if SECRETS.detect_language_before_queueing:
        model = WhisperModel(
            "large-v2",
            device="cpu",
            compute_type="int8",
            download_root="./whisper_models",
        )

    # Loop over all files from telegram db
    with orm.db_session():
        messages: list[TelegramMessage] = list(
            orm.select(
                t for t in TelegramMessage if (
                    t.linked_transcription is None and t.download_status == Status.COMPLETED.name
                    and t.extracted_mp3_size_bytes is not None
                )
            ).order_by(TelegramMessage.file_size_bytes)
        )
    last_logger_print = 0
    for message in messages:
        if time.perf_counter() - last_logger_print > 60:
            last_logger_print = time.perf_counter()
            done, total, done_bytes, total_bytes = TelegramMessage.get_count_without_transcription()
            logger.info(
                f"Uploads remaining {total - done}, "
                f"uploads size remaining {humanize.naturalsize(total_bytes - done_bytes)}, "
                f"uploads size total {humanize.naturalsize(total_bytes)}"
            )
        full_path = message.output_file_path
        if not full_path.is_file():
            logger.error(f"File {full_path} does not exist, skipping")
            continue
        if full_path.match(SECRETS.finder_ignore_glob_pattern):
            continue
        if not full_path.match(SECRETS.finder_add_glob_pattern):
            continue
        if message.downloaded_file_path in uploaded_files:
            with orm.db_session():
                message = TelegramMessage[message.id]
                transcription = TranscriptionJob.get(local_file=message.downloaded_file_path)
                if transcription is None:
                    logger.error("Transcription not found even though file was already uploaded?")
                    continue
                if message.linked_transcription is None:
                    message.linked_transcription = transcription
                else:
                    logger.error(f"File {full_path} was already linked, why is this parsed?")
            logger.warning(f"File {full_path} already uploaded, skipping")
            uploaded_files.add(message.downloaded_file_path)
            continue
        # TODO Skip if it already has a srt or txt transcription

        file_size_bytes = full_path.stat().st_size

        # Detect language if file is big enough
        language_code = ""
        with full_path.open("rb") as f:
            file_data: BytesIO = BytesIO(f.read())
        if (
            SECRETS.detect_language_before_queueing
            and SECRETS.detect_language_before_queueing_min_size_bytes < file_size_bytes
        ):
            _, info = model.transcribe(file_data)
            language_code = info.language

        # Upload file to db
        logger.debug(
            f"Uploading {file_size_bytes/2**20:.1f} mb {message.file_size_bytes/2**20:.1f} mb {full_path.absolute()}"
        )
        with orm.db_session():
            message = TelegramMessage[message.id]
            transcription_job = TranscriptionJob(
                local_file=message.downloaded_file_path,
                task=Task.Transcribe.name,
                forced_language=language_code,
                model_size=ModelSize.Small.name,
                status=JobStatus.QUEUED.name,
                input_file_size_bytes=file_size_bytes,
            )
            transcription_job.input_file_mp3 = TranscriptionMp3File(
                job_item=transcription_job, mp3_data=file_data.getvalue()
            )
            # Link to telegram message
            message.linked_transcription = transcription_job
        uploaded_files.add(message.downloaded_file_path)
    logger.warning("Done uploading files!")


async def link_local_files_to_telegram_messages():
    """Helper functions to get lost files back into the db."""
    with orm.db_session():
        completed_messages: list[TelegramMessage] = list(
            orm.select(t for t in TelegramMessage if t.download_status == Status.COMPLETED.name)
        )
        unique_id_to_message: dict[str, TelegramMessage] = {m.file_unique_id: m for m in completed_messages}

        for path in recurse_path(SECRETS_FULL.TelegramDownloader.output_folder_path, depth=10):
            if path.is_dir():
                continue
            # Link files to db
            if path.stem in unique_id_to_message:
                relative_path = str(path.relative_to(SECRETS_FULL.TelegramDownloader.output_folder_path))
                message = unique_id_to_message[path.stem]
                if message.downloaded_file_path != relative_path:
                    message.downloaded_file_path = relative_path
                    logger.warning(f"Linked {relative_path} to db entry {message.id}")


async def link_telegram_messages_to_transcription_jobs():
    """Link all telegram messages to their transcription jobs in case they do not have a link yet."""
    with orm.db_session():
        uploaded_files: set[str] = set(orm.select(j.local_file for j in TranscriptionJob))
        messages_without_link: list[TelegramMessage] = list(
            orm.select(t for t in TelegramMessage if t.linked_transcription is None and t.file_unique_id != "")
        )
    for message in messages_without_link:
        if message.downloaded_file_path in uploaded_files:
            transcriptions = list(
                orm.select(t for t in TranscriptionJob if t.local_file == message.downloaded_file_path).limit(2)
            )
            with orm.db_session():
                message = TelegramMessage[message.id]
                if len(transcriptions) == 0:
                    # Transcription doesnt exist, file wasnt uploaded yet
                    pass
                elif len(transcriptions) == 1:
                    transcription_job = transcriptions[0]
                    message.linked_transcription = transcription_job
                    logger.info(f"Linked {message.downloaded_file_path} to {transcription_job.id}")
                else:
                    # Delete all transcriptions because duplicate file
                    orm.delete(t for t in TranscriptionJob if t.local_file == message.downloaded_file_path)


async def main():
    # await link_telegram_messages_to_transcription_jobs()
    # await add_processing_jobs_from_file()
    await add_from_telegram_message()


if __name__ == "__main__":
    asyncio.run(main())
