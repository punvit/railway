"""Application configuration using pydantic-settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    database_url: str = "postgresql+asyncpg://channel_manager:channel_manager_secret@localhost:5432/channel_manager"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Lock settings
    lock_ttl_seconds: int = 30
    lock_retry_attempts: int = 3
    lock_retry_delay_ms: int = 100
    
    # Application
    app_name: str = "Hotel Channel Manager"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    @property
    def async_database_url(self) -> str:
        """Ensure database URL uses asyncpg driver."""
        url = self.database_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://") and "+asyncpg" not in url:
             url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
