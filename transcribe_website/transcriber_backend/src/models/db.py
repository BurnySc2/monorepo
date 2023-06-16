"""
Import all models from this file to ensure that they are registered with PonyORM.
"""
from __future__ import annotations

import zipfile
from io import BytesIO

from pony import orm  # pyre-fixme[21]

from src.models import db
from src.models.telegram_model import Status, TelegramChannel, TelegramMessage
from src.models.transcribe_model import (
    JobStatus,
    ModelSize,
    Task,
    TranscriptionJob,
    TranscriptionMp3File,
    TranscriptionResult,
)
from src.secrets_loader import SECRETS as SECRETS_FULL

SECRETS = SECRETS_FULL.Transcriber

__all__ = [
    TelegramChannel,
    TelegramMessage,
    Status,
    TranscriptionJob,
    TranscriptionMp3File,
    TranscriptionResult,
    JobStatus,
    ModelSize,
    Task,
]

db.bind(
    provider=SECRETS.postgres_provider,
    user=SECRETS.postgres_user,
    database=SECRETS.postgres_database,
    password=SECRETS.postgres_password,
    host=SECRETS.postgres_host,
    port=SECRETS.postgres_port,
)

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
        print(orm.select(j for j in TranscriptionJob).get_sql())
        for job in orm.select(j for j in TranscriptionJob):
            print(job.id)
