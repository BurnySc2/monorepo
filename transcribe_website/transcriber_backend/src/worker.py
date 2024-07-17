from __future__ import annotations

import asyncio
import datetime
import logging
import os
import sys
import time
from dataclasses import dataclass
from io import BytesIO
from typing import ClassVar, Literal

import av
import humanize

# pyre-fixme[21]
from faster_whisper import (
    WhisperModel,
    download_model,
)
from loguru import logger
from pony import orm  # pyre-fixme[21]

from src.models.db import JobStatus, TranscriptionJob, compress_files, generate_srt_data, generate_txt_data
from src.models.transcribe_model import TranscriptionResult  # noqa: E402
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

SECRETS = SECRETS_FULL.Transcriber

logging.getLogger("faster_whisper").setLevel(logging.CRITICAL)
logging.getLogger("libav.mp3").setLevel(logging.CRITICAL)


def loguru_handler(record):
    level = record.levelname.upper()
    message = record.getMessage()
    logger.log(level, message)


PONY_DEBUG = os.getenv("PONY_DEBUG") == "True"
if PONY_DEBUG:
    pony_logger = logging.getLogger("pony.orm")
    pony_logger.setLevel(logging.DEBUG)
    pony_logger.addHandler(logging.StreamHandler())
    pony_logger.handlers[-1].emit = loguru_handler


@dataclass
class Worker:
    job_to_task_map: ClassVar[dict[int, asyncio.Task]] = {}
    loaded_model: ClassVar[WhisperModel] = None  # pyre-fixme[11]
    loaded_model_language: ClassVar[Literal["multilingual", "en"]] = "multilingual"

    # Instance specific attributes
    job_id: int
    started: datetime.datetime

    @staticmethod
    async def work_model_size(model_size: str, use_english_model: bool = False) -> None:
        # Get all jobs of this model size
        job_count_of_this_model = TranscriptionJob.get_count_by_model_size(model_size, english=use_english_model)
        if job_count_of_this_model == 0:
            # If no such jobs exist, return early
            return

        # Before starting worker: download model and load as class variable
        working_model_size = f"{model_size}.en" if use_english_model and "large" not in model_size else model_size

        # Download model
        logger.info(f"Downloading model: {working_model_size}")
        download_model(working_model_size, cache_dir="./whisper_models")

        # Load model to memory and save as class variable
        logger.info(f"Loading model to memory: {working_model_size}")
        Worker.loaded_model = WhisperModel(
            working_model_size,
            device="cpu",
            compute_type="int8",
            download_root="./whisper_models",
            # Changing number of workers or threads doesnt seem to affect speed on multi-core pc
            # https://github.com/guillaumekln/faster-whisper/issues/100#issuecomment-1492141352
            # num_workers=8,
            # cpu_threads=2,
        )
        Worker.loaded_model_language = "multilingual"
        if working_model_size.endswith(".en"):
            Worker.loaded_model_language = "en"

        last_report_print = 0
        while 1:
            # If no more jobs of this model size, wait for tasks to complete before loading next model
            if TranscriptionJob.get_count_by_model_size(model_size, english=use_english_model) == 0:
                while len(Worker.job_to_task_map) > 0:
                    await asyncio.sleep(1)
                return

            if last_report_print + 60 < time.time():
                last_report_print = time.time()
                (
                    processing_per_second,
                    remaining_time_seconds,
                ) = TranscriptionJob.get_processing_rate_and_remaining_time()
                logger.info(
                    f"Status: {humanize.naturalsize(processing_per_second * 3600 * 24)} per day, "
                    f"estimated remaining time: {humanize.precisedelta(remaining_time_seconds)}"
                )

            # Start worker and use this model instance to transcribe

            # Wait while worker limit is reached
            while len(Worker.job_to_task_map) >= SECRETS.workers_limit:
                await asyncio.sleep(1)

            # Get next job (matching model size) and mark as processing
            next_job = TranscriptionJob.get_one_queued(model_size, english=use_english_model, mark_as_accepted=True)
            if next_job is None:
                logger.info("No more jobs to process, waiting for jobs to complete")
                continue
            # Start worker
            worker = Worker(next_job.id, started=datetime.datetime.utcnow())
            Worker.job_to_task_map[next_job.id] = asyncio.create_task(worker.work_and_catch_exception())
            # Let worker mark job as done

    async def work_and_catch_exception(self) -> None:
        try:
            await self.work()
            Worker.job_to_task_map.pop(self.job_id)
        except Exception as e:  # noqa: BLE001
            # TODO set error in db?
            logger.exception(e)
            sys.exit(1)

    async def work(self) -> None:
        """
        # TODO
        This function may encounter
        pony.orm.dbapiprovider.OperationalError
        and needs to be caught and auto-restarted or auto-continued
        """
        done_count, total_count, _, _ = TranscriptionJob.get_count()
        transcription_start_time = time.perf_counter()

        with orm.db_session():
            job_info: TranscriptionJob = TranscriptionJob[self.job_id]
            job_info.status = JobStatus.PROCESSING.name
            # Load mp3 file from owncloud
            mp3_data: BytesIO = BytesIO(job_info.mp3_data)
            transcription_language = (
                "en" if (job_info.forced_language == "en" or job_info.detected_language == "en") else None
            )
            mp3_data_size_bytes: int = mp3_data.getbuffer().nbytes
        try:
            # Initialize transcribing
            segments, info = Worker.loaded_model.transcribe(mp3_data, language=transcription_language)
        except av.error.ValueError:
            # Unable to read mp3 file
            with orm.db_session():
                job_info: TranscriptionJob = TranscriptionJob[self.job_id]
                job_info.status = JobStatus.AV_ERROR.name
                # Delete mp3 file
                job_info.delete_mp3_from_owncloud()
                job_info.input_file_mp3_owncloud_path = None
            # logger.warning(f"Worker: Error with job id {self.job_id}")
            return
        if transcription_language is None:
            # Extract language from file
            transcription_language = info.language
        if job_info.detected_language == "":
            # Update language in db
            with orm.db_session():
                job_info: TranscriptionJob = TranscriptionJob[self.job_id]
                job_info.detected_language = transcription_language
            logger.info(f"Set detected language to '{transcription_language}' for job id {self.job_id}")
        if transcription_language == "en" and Worker.loaded_model_language != "en":
            # Currently loaded is multilingual, not english
            # But detected language is english
            with orm.db_session():
                job_info: TranscriptionJob = TranscriptionJob[self.job_id]
                job_info.status = JobStatus.QUEUED.name
                job_info.job_started = None
            return

        logger.info(f"Worker: (Remaining: {total_count - done_count}) Started job id {self.job_id}")

        # Start tanscribing
        transcribed_data: list[tuple[float, float, str]] = []
        old_percentage_value: int = 0
        total_mp3_duration = int(info.duration)
        for segment in segments:
            transcribed_data.append((segment.start, segment.end, segment.text.lstrip()))
            # Update progress in database only if mp3 is large
            new_percentage_value = int(100 * segment.end / total_mp3_duration)
            old_percentage_value = TranscriptionJob.update_progress(
                self.job_id,
                new_progress=new_percentage_value,
                old_progress=old_percentage_value,
                mp3_data_size=mp3_data_size_bytes,
            )

        # Done transcribing, write srt and txt file to db
        txt_data: str = generate_txt_data(transcribed_data)
        srt_data: str = generate_srt_data(transcribed_data)
        srt_original_zipped: BytesIO = compress_files(
            {
                "transcribed.srt": srt_data,
            }
        )
        with orm.db_session():
            job_info: TranscriptionJob = TranscriptionJob[self.job_id]
            job_info.job_completed = datetime.datetime.utcnow()
            job_info.progress = 100
            job_info.status = JobStatus.DONE.name
            # pyre-fixme[28]
            job_info.output_data = TranscriptionResult(
                job_item=job_info,
                srt_original_zipped=srt_original_zipped.getvalue(),
                txt_original=txt_data,
            )
            # Delete mp3 file
            job_info.delete_mp3_from_owncloud()
            job_info.input_file_mp3_owncloud_path = None

        duration = time.perf_counter() - transcription_start_time
        logger.info(f"Worker: Completed job id {self.job_id} after {humanize.precisedelta(int(duration))}")
        # Uncomment when running scalene to run 1 transcription
        # exit(0)


async def main():
    # Dont run if system just booted up
    while time.clock_gettime(time.CLOCK_BOOTTIME) < 600:
        await asyncio.sleep(1)

    # Select and mark all jobs for update (=lock)
    # - that are "processing" and processing job started too long ago
    # - that were accepted too long ago
    # mark those as "queued" again
    time_4h_ago = datetime.datetime.utcnow() - datetime.timedelta(seconds=3600 * 4)
    with orm.db_session():
        jobs = orm.select(
            j
            for j in TranscriptionJob
            if (j.job_started is None or j.job_started < time_4h_ago)
            and j.status
            in [
                JobStatus.ACCEPTED.name,
                JobStatus.PROCESSING.name,
                JobStatus.FINISHING.name,
            ]
        ).for_update()
        for job in jobs:
            job.status = JobStatus.QUEUED.name
            job.job_started = None
            job.progress = 0
            job.remaining_retries -= 1

    # TODO Figure out memory usage of each model
    # Then calculate from free memory if a job of certain size can be accepted,
    # otherwise reduce model size to reduce memory usage?

    for model_size in SECRETS.workers_acceptable_models:
        # Always use multilingual model first to detect language and then use english model
        await Worker.work_model_size(model_size, use_english_model=False)
        await Worker.work_model_size(model_size, use_english_model=True)
    logger.info("Worker: Done with all jobs! Waiting for new jobs...")


if __name__ == "__main__":
    asyncio.run(main())
