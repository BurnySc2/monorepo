"""
Database models for supabase
"""
from __future__ import annotations

import datetime
import enum
import zipfile
from io import BytesIO
from pathlib import Path

import arrow
from pony import orm  # pyre-fixme[21]

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


db = orm.Database()

db.bind(
    provider=SECRETS.postgres_provider,
    user=SECRETS.postgres_user,
    database=SECRETS.postgres_database,
    password=SECRETS.postgres_password,
    host=SECRETS.postgres_host,
    port=SECRETS.postgres_port,
)


# pyre-fixme[11]
class Mp3File(db.Entity):
    _table_ = "transcribe_mp3s"  # Table name
    id = orm.PrimaryKey(int, auto=True)
    job_item = orm.Required("JobItem")
    # The mp3 file to be analyzed
    mp3_data = orm.Optional(bytes)


class OutputResult(db.Entity):
    _table_ = "transcribe_text"  # Table name
    id = orm.PrimaryKey(int, auto=True)
    job_item = orm.Required("JobItem")
    # Could zip the files but then unable to query them
    srt_original_zipped = orm.Optional(bytes)
    txt_original = orm.Optional(orm.LongStr)


class JobItem(db.Entity):
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

    input_file_mp3 = orm.Optional(Mp3File, cascade_delete=True)
    input_file_size_bytes = orm.Optional(int, size=64)
    # input_file_duration = orm.Optional(int, size=32)
    output_data = orm.Optional(OutputResult, cascade_delete=True)

    issued_by = orm.Optional(str)
    # The full path to the .mp3 file, dont add duplicates
    local_file = orm.Optional(str, unique=True)
    status = orm.Optional(str)
    progress = orm.Optional(int, default=0)

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
    def get_one_queued(acceptable_models: list[str] | None = None) -> JobItem | None:
        """Used in getting any queued jobs for the processing-worker."""
        with orm.db_session():
            if acceptable_models is None:
                job_items = orm.select(
                    # pyre-fixme[16]
                    j for j in JobItem if j.status == JobStatus.QUEUED.name and j.remaining_retries > 0
                ).order_by(
                    JobItem.job_created,
                ).limit(1)
            else:
                # Filter jobs that have inacceptable model sizes (e.g. machine has too low ram to use large model)
                job_items = orm.select(
                    j for j in JobItem if j.status == JobStatus.QUEUED.name and j.model_size in acceptable_models
                    and j.remaining_retries > 0
                ).order_by(
                    JobItem.job_created,
                ).limit(1)
            if len(job_items) == 0:
                return None
            return list(job_items)[0]


# Enable debug mode to see the queries sent
# orm.set_sql_debug(True)

db.generate_mapping(create_tables=True)


def compress_files(files: dict[str, str]) -> BytesIO:
    zip_data = BytesIO()
    with zipfile.ZipFile(zip_data, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zip_file:
        for file_name, file_content in files.items():
            zip_file.writestr(file_name, file_content)
    return zip_data


def decompress_files(zip_file: BytesIO) -> dict[str, str]:
    decompressed = {}
    with zipfile.ZipFile(zip_file, mode="r") as zip_file:
        for file_name in zip_file.namelist():
            with zip_file.open(file_name, mode="r") as file:
                decompressed[file_name] = file.read().decode()
    return decompressed


if __name__ == "__main__":
    with orm.db_session():
        # pyre-fixme[16]
        print(orm.select(j for j in JobItem).get_sql())
        for job in orm.select(j for j in JobItem):
            print(type(job.job_parameters))
            print(job.job_parameters)
