"""Central application settings loaded from environment variables."""

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Single typed settings object mirroring .env.example keys."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    postgres_connection_string: str = Field(default="postgresql://postgres:password@domain.com/litestar_server")

    # Server and frontend
    backend_domain: str = Field(default="backend-domain.com")
    backend_server_url: str = Field(default="http://localhost:8000")
    backend_ws_server_url: str = Field(default="wss:backend-domain.com")
    frontend_url: str = Field(default="http://localhost:5173")
    stage: str = Field(default="dev")

    # RustFS S3 storage
    rustfs_s3_url: str = Field(default="http://0.0.0.0:9000")
    rustfs_access_key: str | None = Field(default=None)
    rustfs_secret_key: str | None = Field(default=None)
    rustfs_audiobook_bucket: str = Field(default="rustfs-audiobook-bucket")
    rustfs_telegram_bucket: str = Field(default="rustfs-telegram-bucket")
    rustfs_sc2_replays_bucket: str = Field(default="sc2-replays")
    rustfs_admin_url: str = Field(default="http://localhost:3903")
    rustfs_admin_token: str | None = Field(default=None)
    rustfs_telegram_bucket_expiration_days: int = Field(default=7)

    # Audiobook converter
    audiobook_convert_estimate_factor: float = Field(default=0.3)
    audiobook_max_concurrent_conversions: int = Field(default=1)

    # TikTok TTS
    tiktok_session_id: str | None = Field(default=None)

    # OAuth providers (dev defaults for localhost login - override via env in prod)
    github_app_client_id: str | None = Field(default="1c200ded47490cce3b4d")
    github_app_client_secret: str | None = Field(default="2aab3b1a609cb1a4126c7eec121bad2343332113")
    twitch_app_client_id: str | None = Field(default="ddgeuklh32bi15odtfc0o7gu4g4ehn")
    twitch_app_client_secret: str | None = Field(default="mtu72a2v35p8x7f4fddwmzc2wwdruu")
    google_app_client_id: str | None = Field(
        default="359432605842-cm653in48c8itjpk40j6vjcottc7541i.apps.googleusercontent.com"
    )
    google_app_client_secret: str | None = Field(default="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")
    facebook_app_client_id: str | None = Field(default="1668878523656479")
    facebook_app_client_secret: str | None = Field(default="dcd070e77fab0aabf1d468fe1d586e28")

    # Telegram browser allowlist
    allowed_twitch_users_for_telegram_browser: str = Field(default="")

    # Language data and cache
    nltk_data_dir: str = Field(default="./data/nltk")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
