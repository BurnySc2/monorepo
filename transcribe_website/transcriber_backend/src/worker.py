from __future__ import annotations

import asyncio
import sys
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import ClassVar

from faster_whisper import download_model
from loguru import logger
from secrets_loader import SECRETS

sys.path.append(str(Path(__file__).parent.parent))

from src.db import JobItem, JobStatus, OutputResult, orm


@dataclass
class Worker:
    active_worker_count: ClassVar[int] = 0
    job_id: int = 0

    async def work(self) -> None:
        with orm.db_session():
            job_info: JobItem = JobItem[self.job_id]
            mp3_data: BytesIO = BytesIO(job_info.input_file_mp3.mp3_data)
            job_info.status = JobStatus.PROCESSING.name
        logger.info(f"Worker: Started job id {self.job_id}")
        process = await asyncio.subprocess.create_subprocess_exec(
            *[
                "docker",
                "run",
                "--rm",
                "-i",
                "--name",
                f"temp_transcribe_{self.job_id}",
                "--entrypoint",
                "poetry",
                "--volume",
                f"{SECRETS.models_root}:/app/whisper_models",
                "transcriber_image",
                "run",
                "python",
                "src/argparser.py",
                "--input_file",
                "-",
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
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Process job
        stdout_data, stderr_data = await process.communicate(mp3_data.getvalue())
        if stdout_data == b"":  # or stderr_data != b"":
            logger.error(f"There has been an error with job {self.job_id}:\n{stderr_data.decode()}")
            Worker.active_worker_count -= 1
            return
        # Upload data to db
        with orm.db_session():
            job_info: JobItem = JobItem[self.job_id]
            result_database_entry: OutputResult = OutputResult(
                job_item=job_info,
                zip_data=stdout_data,
            )
            job_info.output_zip_data = result_database_entry
            job_info.status = JobStatus.DONE.name
        logger.info(f"Worker: Completed job id {self.job_id}")
        Worker.active_worker_count -= 1


async def main():
    # Build docker image to have the most up to date python files included
    proc = await asyncio.subprocess.create_subprocess_exec(
        *[
            "docker",
            "build",
            "-t",
            "transcriber_image",
            ".",
        ],
        # stdin=asyncio.subprocess.DEVNULL,
        stderr=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.DEVNULL,
    )
    await proc.communicate()

    def done_callback(future):
        future.result()

    while 1:
        while Worker.active_worker_count >= SECRETS.workers_limit:
            # TODO if worker has been active for too long, cancel
            await asyncio.sleep(1)
        job: JobItem | None = JobItem.get_one_queued()
        if job is None:
            await asyncio.sleep(10)
            continue

        # Before starting worker: download model
        # TODO Download all models? DL english models
        download_model(job.model_size.lower(), cache_dir=SECRETS.models_root)
        with orm.db_session():
            job_info: JobItem = JobItem[job.id]
            job_info.status = JobStatus.ACCEPTED.name
        # Start worker
        worker = Worker(job_id=job_info.id)
        Worker.active_worker_count += 1
        task = asyncio.create_task(worker.work())
        # TODO Create stacktrace if task errors
        task.add_done_callback(done_callback)


if __name__ == "__main__":
    asyncio.run(main())
