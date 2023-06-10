import datetime
from pathlib import Path
from typing import Literal

import toml
from pydantic import BaseModel


class TranscriberSecrets(BaseModel):
    stage: Literal["DEV", "PROD"] = "DEV"

    postgres_provider: str = ""
    postgres_user: str = ""
    postgres_database: str = ""
    postgres_password: str = ""
    postgres_host: str = ""
    postgres_port: str = ""

    workers_limit: int = 1
    workers_acceptable_models: list[str] = ["Tiny", "Base", "Small"]
    detect_language_before_queueing: bool = True
    detect_language_before_queueing_min_size_bytes: int = 10_000_000

    finder_add_glob_pattern: str = ""
    finder_ignore_glob_pattern: str = ""
    finder_folders_to_parse: list[str] = []


class TelegramDownloaderSecrets(BaseModel):
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
    
class Secrets(BaseModel):
    TelegramDownloader: TelegramDownloaderSecrets = TelegramDownloaderSecrets()
    Transcriber: TranscriberSecrets = TranscriberSecrets()


with (Path(__file__).parent.parent / "SECRETS.toml").open() as f:
    toml_data = toml.loads(f.read())
    SECRETS: Secrets = Secrets.parse_obj(toml_data)
