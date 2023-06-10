from __future__ import annotations

import asyncio
import datetime
import sys
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import ClassVar

from faster_whisper import download_model  # pyre-fixme[21]
from loguru import logger

sys.path.append(str(Path(__file__).parent.parent))

from src.db_transcriber import JobItem, JobStatus, orm  # noqa: E402
from src.secrets_loader import SECRETS as SECRETS_FULL  # noqa: E402

SECRETS = SECRETS_FULL.Transcriber


@dataclass
class Worker:
    active_workers: ClassVar[list[Worker]] = []
    job_to_task_map: ClassVar[dict[int, asyncio.Task]] = {}
    job_id: int
    started: datetime.datetime

    async def work(self) -> None:
        with orm.db_session():
            # pyre-fixme[16]
            job_info: JobItem = JobItem[self.job_id]
            mp3_data: BytesIO = BytesIO(job_info.input_file_mp3.mp3_data)
        logger.info(f"Worker: Started job id {self.job_id}")
        process = await asyncio.subprocess.create_subprocess_exec(
            *[
                "poetry",
                "run",
                "python",
                "src/argparser.py",
                "--input_file",
                "-",
                "--database_job_id",
                f"{job_info.id}",
                "--task",
                f"{job_info.task}",
                # "--language",
                # "en",
                "--model",
                f"{job_info.model_size}",
                "--output_file",
                "-",
            ],
            stdin=asyncio.subprocess.PIPE,
            # Comment out to see errors
            # stdout=asyncio.subprocess.DEVNULL,
            # stderr=asyncio.subprocess.DEVNULL,
        )
        # Process job
        await process.communicate(mp3_data.getvalue())
        # Upload data to db already done from worker

        logger.info(f"Worker: Completed job id {self.job_id}")
        Worker.active_workers.remove(self)


async def main():
    # Dont run if system just booted up
    while time.clock_gettime(time.CLOCK_BOOTTIME) < 600:
        await asyncio.sleep(1)

    # Select and mark all jobs for update (=lock)
    # - that are "processing" and processing job started too long ago
    # - that were accepted too long ago
    # mark those as "queued" again
    time_1h_ago = datetime.datetime.utcnow() - datetime.timedelta(seconds=3600)
    with orm.db_session():
        jobs = orm.select(
            j for j in JobItem if (j.job_started is None or j.job_started < time_1h_ago) and j.status in [
                JobStatus.ACCEPTED.name,
                JobStatus.PROCESSING.name,
                JobStatus.FINISHING.name,
            ]
        ).for_update()
        for job in jobs:
            job.status = JobStatus.QUEUED.name
            job.progress = 0
            job.remaining_retries -= 1

    def done_callback(future):
        future.result()

    while 1:
        while len(Worker.active_workers) >= SECRETS.workers_limit:
            # If worker has been active for too long, cancel
            for worker in Worker.active_workers:
                if (datetime.datetime.utcnow() - worker.started).total_seconds() > 3600:
                    logger.warning(f"Worker on job_id {worker.job_id} has taken more than 3600 seconds. Cancelling job")
                    # Stop asyncio task
                    Worker.job_to_task_map.pop(worker.job_id).cancel()
                    Worker.active_workers.remove(worker)
                    break
            await asyncio.sleep(1)
        job: JobItem | None = JobItem.get_one_queued(SECRETS.workers_acceptable_models)
        if job is None:
            await asyncio.sleep(10)
            continue

        # Before starting worker: download model
        # Download international model
        download_model(job.model_size.lower(), cache_dir="./whisper_models")
        if ".en" not in job.model_size and "large" not in job.model_size.lower():
            # Download english model
            download_model(f"{job.model_size.lower()}.en", cache_dir="./whisper_models")

        with orm.db_session():
            job_info: JobItem = JobItem[job.id]
            job_info.status = JobStatus.ACCEPTED.name
        # Start worker
        worker = Worker(
            job_id=job_info.id,
            started=datetime.datetime.utcnow(),
        )
        Worker.active_workers.append(worker)
        task = asyncio.create_task(worker.work())
        Worker.job_to_task_map[worker.job_id] = task
        # TODO Create stacktrace if task errors
        task.add_done_callback(done_callback)


if __name__ == "__main__":
    asyncio.run(main())
