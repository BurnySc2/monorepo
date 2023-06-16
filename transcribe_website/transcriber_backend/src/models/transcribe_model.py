"""
Database models for supabase
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
    def get_one_queued(acceptable_models: list[str] | None = None) -> TranscriptionJob | None:
        """Used in getting any queued jobs for the processing-worker."""
        with orm.db_session():
            if acceptable_models is None:
                job_items = orm.select(
                    # pyre-fixme[16]
                    j for j in TranscriptionJob if j.status == JobStatus.QUEUED.name and j.remaining_retries > 0
                ).order_by(
                    TranscriptionJob.job_created,
                ).limit(1)
            else:
                # Filter jobs that have inacceptable model sizes (e.g. machine has too low ram to use large model)
                job_items = orm.select(
                    j for j in TranscriptionJob if j.status == JobStatus.QUEUED.name
                    and j.model_size in acceptable_models and j.remaining_retries > 0
                ).order_by(
                    TranscriptionJob.job_created,
                ).limit(1)
            if len(job_items) == 0:
                return None
            return list(job_items)[0]

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
