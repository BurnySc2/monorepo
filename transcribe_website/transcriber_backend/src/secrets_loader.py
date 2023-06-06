from pathlib import Path
from typing import Literal

import toml
from pydantic import BaseModel


class Secrets(BaseModel):
    stage: Literal["DEV", "PROD"] = "DEV"

    postgres_provider: str = ""
    postgres_user: str = ""
    postgres_database: str = ""
    postgres_password: str = ""
    postgres_host: str = ""
    postgres_port: str = ""

    models_root: str = ""

    workers_limit: int = 1

    finder_add_glob_pattern: str = ""
    finder_ignore_glob_pattern: str = ""
    finder_folders_to_parse: list[str] = []


with (Path(__file__).parent.parent / "SECRETS.toml").open() as f:
    SECRETS: Secrets = Secrets(**toml.loads(f.read()))
