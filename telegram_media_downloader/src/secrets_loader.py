import datetime
from pathlib import Path
from typing import Literal

import toml
from pydantic import BaseModel


class Secrets(BaseModel):
    api_id: int = 123456789
    api_hash: str = "some.default.hash"
    channel_ids: list[str] = ["somechannel"]
    stage: Literal["DEV", "PROD"] = "DEV"
    media_types: set[str] = {"audio", "image", "video"}
    extract_audio_from_videos: bool = True
    output_folder: str = ""
    parallel_downloads_count: int = 1
    # Filters
    media_min_date: datetime.datetime = datetime.datetime.fromisoformat("0001-01-01T00:00:00-00:00")
    media_max_date: datetime.datetime = datetime.datetime.fromisoformat("9999-01-01T00:00:00-00:00")
    # Photo
    photo_min_file_size_bytes: int = 0
    photo_max_file_size_bytes: int = 4_000_000_000
    photo_min_width: int = 0
    photo_max_width: int = 1_000_000
    photo_min_height: int = 0
    photo_max_height: int = 1_000_000
    # Video
    video_min_file_size_bytes: int = 0
    video_max_file_size_bytes: int = 4_000_000_000
    video_min_file_duration_seconds: int = 0
    video_max_file_duration_seconds: int = 4_000_000_000
    video_min_width: int = 0
    video_max_width: int = 1_000_000
    video_min_height: int = 0
    video_max_height: int = 1_000_000
    # Audio
    audio_min_file_size_bytes: int = 0
    audio_max_file_size_bytes: int = 4_000_000_000
    audio_min_file_duration_seconds: int = 0
    audio_max_file_duration_seconds: int = 4_000_000_000

    @property
    def output_folder_path(self) -> Path:
        return Path(self.output_folder)


with (Path(__file__).parent.parent / "SECRETS.toml").open() as f:
    SECRETS = Secrets(**toml.loads(f.read()))
