from __future__ import annotations

from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.

    Uses a .env file in development. All values are safe defaults where possible.
    """

    mcp_server_name: str = "MediaAggregatorMCP"

    # Defaults
    default_region: str = "IN"
    default_limit: int = 20

    # HTTP settings
    request_timeout_seconds: int = 15
    request_max_retries: int = 2
    request_retry_backoff_seconds: float = 0.5

    # API keys / credentials
    youtube_api_key: Optional[str] = None
    newsapi_key: Optional[str] = None

    reddit_client_id: Optional[str] = None
    reddit_client_secret: Optional[str] = None
    reddit_user_agent: Optional[str] = None

    # AuthKit settings
    authkit_domain: Optional[str] = None
    base_url: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()


