"""
Database models for postgres
"""
from __future__ import annotations

import datetime
import enum
from pathlib import Path

import arrow
from pony import orm  # pyre-fixme[21]

from src.models import db
from src.secrets_loader import SECRETS as SECRETS_FULL

SECRETS = SECRETS_FULL.Transcriber


class Task(enum.Enum):
    Transcribe = 0
    Translate = 1
    Detect = 2


class ModelSize(enum.Enum):
    Tiny = 0
    Base = 1
    Small = 2
    Medium = 3
    Large = 4


class JobStatus(enum.Enum):
    UNKNOWN = 0
    QUEUED = 1  # Ready to be processed
    ACCEPTED = 2  # Accepted by a backend transcriber
    PROCESSING = 3  # Files have been downloaded and progress started
    FINISHING = 4  # Transcribing is completed, uploading results
    DONE = 5  # Results uploaded to db
    AV_ERROR = 6


# pyre-fixme[11]
class TranscriptionMp3File(db.Entity):
    _table_ = "transcribe_mp3s"  # Table name
    id = orm.PrimaryKey(int, auto=True)
    job_item = orm.Required("TranscriptionJob")
    # The mp3 file to be analyzed
    mp3_data = orm.Optional(bytes)


class TranscriptionResult(db.Entity):
    _table_ = "transcribe_text"  # Table name
    id = orm.PrimaryKey(int, auto=True)
    job_item = orm.Required("TranscriptionJob")
    # Could zip the files but then unable to query them
    srt_original_zipped = orm.Optional(bytes)
    txt_original = orm.Optional(orm.LongStr)


class TranscriptionJob(db.Entity):
    _table_ = "transcribe_jobs"  # Table name
    # id maps to f"{id}.mp3" in bucket "transcribe_mp3"
    id = orm.PrimaryKey(int, auto=True)
    # When the job was queued - when did the user issue the job?
    job_created = orm.Optional(datetime.datetime, default=datetime.datetime.utcnow)
    # When the job has started processing
    job_started = orm.Optional(datetime.datetime)
    # When the job completed processing
    job_completed = orm.Optional(datetime.datetime)
    # Do not retry jobs with retry <= 0
    remaining_retries = orm.Optional(int, default=3)
    # task - (TRANSCRIBE, TRANSLATE, DETECT_LANGUAGE)
    task = orm.Required(str, py_check=lambda val: Task[val])
    # language - (en, de, ...)
    forced_language = orm.Optional(str)
    detected_language = orm.Optional(str)
    # model_size - (tiny, base, small, medium, large)
    model_size = orm.Required(str, py_check=lambda val: ModelSize[val])

    input_file_mp3 = orm.Optional(TranscriptionMp3File, cascade_delete=True)
    input_file_size_bytes = orm.Optional(int, size=64)
    # input_file_duration = orm.Optional(int, size=32)
    output_data = orm.Optional(TranscriptionResult, cascade_delete=True)

    issued_by = orm.Optional(str)
    # The full path to the .mp3 file, dont add duplicates
    local_file = orm.Required(str, unique=True)
    status = orm.Optional(str)
    progress = orm.Optional(int, default=0)
    # The telegram message that may have triggered this job
    related_telegram_message = orm.Optional("TelegramMessage")

    @classmethod
    def from_tuple(cls, job_tuple: tuple) -> TranscriptionJob:
        entity_dict = {col_name: value for col_name, value in zip(cls._columns_, job_tuple)}  # pyre-ignore[16]
        return TranscriptionJob(**entity_dict)

    @property
    def job_created_arrow(self) -> arrow.Arrow:
        return arrow.get(self.job_created)

    @property
    def job_started_arrow(self) -> arrow.Arrow:
        return arrow.get(self.job_started)

    @property
    def job_completed_arrow(self) -> arrow.Arrow:
        return arrow.get(self.job_completed)

    @property
    def local_file_path(self) -> Path:
        return Path(self.local_file)

    @staticmethod
    def get_count() -> tuple[int, int, int, int]:
        """Returns a tuple of how many transcriptions are done and how many there are in total.
        Additionally returns size of completed transcriptions and how many total."""
        done_status = [JobStatus.DONE.name]
        total_count_status = [
            JobStatus.QUEUED.name,
            JobStatus.ACCEPTED.name,
            JobStatus.PROCESSING.name,
            JobStatus.FINISHING.name,
            JobStatus.DONE.name,
        ]
        with orm.db_session():
            done_count = orm.count(
                # pyre-fixme[16]
                m for m in TranscriptionJob if m.status in done_status
            )
            total_count = orm.count(m for m in TranscriptionJob if m.status in total_count_status)
            done_bytes = orm.sum(m.input_file_size_bytes for m in TranscriptionJob if m.status in done_status)
            total_bytes = orm.sum(m.input_file_size_bytes for m in TranscriptionJob if m.status in total_count_status)
            return done_count, total_count, done_bytes, total_bytes

    @staticmethod
    def get_processing_rate_and_remaining_time() -> tuple[float, float]:
        """Returns rate in bytes per second and remaining time in seconds."""
        time_1h_ago = datetime.datetime.utcnow() - datetime.timedelta(seconds=3600)
        with orm.db_session():
            size_of_completed_jobs = orm.sum(
                # pyre-fixme[16]
                t.input_file_size_bytes for t in TranscriptionJob
                if t.job_completed is not None and t.job_completed > time_1h_ago
            )
            processing_rate_per_second = size_of_completed_jobs / 3600
            _, _, done_bytes, total_bytes = TranscriptionJob.get_count()
            remaining_bytes = total_bytes - done_bytes
            if processing_rate_per_second == 0:
                remaining_time_seconds = 365 * 420 * 24 * 3600
            else:
                remaining_time_seconds = remaining_bytes / processing_rate_per_second
            return processing_rate_per_second, remaining_time_seconds

    @staticmethod
    def get_count_by_model_size(model_size: str, english: bool = False) -> int:
        with orm.db_session():
            if english:
                # Return jobs with english language - to be used with the english language model
                return orm.count(
                    # pyre-fixme[16]
                    t for t in TranscriptionJob if (
                        t.status == JobStatus.QUEUED.name and t.model_size.lower() == model_size
                        and t.remaining_retries > 0 and (t.forced_language == "en" or t.detected_language == "en")
                    )
                )
            # Return all all jobs that are non-english or have no language set
            return orm.count(
                t for t in TranscriptionJob if (
                    t.status == JobStatus.QUEUED.name and t.model_size.lower() == model_size and t.remaining_retries > 0
                    and (t.forced_language != "en" and t.detected_language != "en")
                )
            )

    @staticmethod
    def get_one_queued(
        model_size: str, english: bool = False, mark_as_accepted: bool = False
    ) -> TranscriptionJob | None:
        """Used in getting any queued jobs for the processing-worker."""
        with orm.db_session():
            if english:
                # Return jobs with english language - to be used with the english language model
                job_items = orm.select(
                    # pyre-fixme[16]
                    t for t in TranscriptionJob if (
                        t.status == JobStatus.QUEUED.name and t.model_size.lower() == model_size
                        and t.remaining_retries > 0 and (t.forced_language == "en" or t.detected_language == "en")
                    )
                ).order_by(
                    TranscriptionJob.job_created,
                ).limit(1)
            else:
                # Return all all jobs that are non-english or have no language set
                job_items = orm.select(
                    t for t in TranscriptionJob if (
                        t.status == JobStatus.QUEUED.name and t.model_size.lower() == model_size
                        and t.remaining_retries > 0 and (t.forced_language != "en" and t.detected_language != "en")
                    )
                ).order_by(
                    TranscriptionJob.job_created,
                ).limit(1)
            if len(job_items) == 0:
                return None
            job_item = job_items[0]
            if mark_as_accepted:
                job_item.status = JobStatus.ACCEPTED.name
                job_item.job_started = datetime.datetime.utcnow()
            return job_item
