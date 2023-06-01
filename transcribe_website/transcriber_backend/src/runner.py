"""
Start docker jobs, poll them (check how long they've been running), cancel stall containers
"""
from __future__ import annotations

from src.db import JobItem


def start_job(job: JobItem) -> str | None:
    """
    Start docker container with job and return its ID
    """


def list_all_jobs() -> list[str]:
    """
    Get all ids of running jobs
    """


def cancel_job(job_id: str):
    """
    Cancel a job
    """


def stop_stale_jobs():
    """
    Cancel all stale jobs
    """
