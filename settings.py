from __future__ import annotations

from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables.
    
    Uses a .env file in development. All values are safe defaults where possible.
    """

    mcp_server_name: str = "FinanceMCP"

    # HTTP settings
    request_timeout_seconds: int = 15
    request_max_retries: int = 3
    request_retry_backoff_seconds: float = 1.0

    # Financial API keys
    alpha_vantage_api_key: Optional[str] = None
    fred_api_key: Optional[str] = None
    
    # Default settings
    default_currency: str = "USD"
    default_market: str = "US"
    default_timeframe: str = "1d"
    
    # Rate limiting settings
    requests_per_minute: int = 60
    cache_ttl_seconds: int = 300  # 5 minutes

    # AuthKit settings (keeping MCPAuth integration)
    auth_issuer: Optional[str] = None
    resource: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"


settings = Settings()
