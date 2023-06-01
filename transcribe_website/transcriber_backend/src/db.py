"""
Database models for supabase
"""
from __future__ import annotations

from pathlib import Path
from typing import Generator, Literal

import arrow
import toml
from postgrest.base_request_builder import APIResponse  # pyre-fixme[21]
from pydantic import BaseModel
from supabase import Client, create_client


class Secrets(BaseModel):
    supabase_url: str = "https://dummyname.supabase.co"
    supabase_key: str = "some.default.key"
    discord_key: str = "somedefaultkey"
    stage: Literal["DEV", "PROD"] = "DEV"


SECRETS_PATH = Path("SECRETS.toml")
assert SECRETS_PATH.is_file(), """Could not find a 'SECRETS.toml' file.
 Make sure to enter variables according to the 'Secrets' class."""

with SECRETS_PATH.open() as f:
    SECRETS = Secrets(**toml.loads(f.read()))

supabase: Client = create_client(SECRETS.supabase_url, SECRETS.supabase_key)


class JobItem(BaseModel):
    id: int = 0
    # When the job was queued - when did the user issue the job?
    job_created: str = ""
    # When the job has started processing
    job_started: str | None = None
    # When the job completed processing
    job_completed: str | None = None
    # Do not retry jobs with retry>=max_retries
    retry: int = 0
    max_retries: int = 0
    # Other job params, e.g.
    # task - (transcribe, translate, detect language)
    # language - (en, de, ...)
    # model - (tiny, base, small, medium, large)
    job_params: dict = {}
    # Always generate a .zip file which contains a .srt file, from which all other formats can be converted
    output_data: str | None = None

    @property
    def job_created_arrow(self) -> arrow.Arrow:
        return arrow.get(self.job_created)

    @property
    def job_started_arrow(self) -> arrow.Arrow:
        return arrow.get(self.job_started)

    @property
    def job_completed_arrow(self) -> arrow.Arrow:
        return arrow.get(self.job_completed)

    @staticmethod
    def table_name() -> str:
        return "transcribe_jobs"

    @staticmethod
    def from_select(response: APIResponse) -> Generator[JobItem, None, None]:
        for row in response.data:
            yield JobItem(**row)


if __name__ == "__main__":
    response = supabase.table(JobItem.table_name()).select("*").order("job_created").execute()
    for row in JobItem.from_select(response):
        # job = JobItem(**row)
        print(row)
