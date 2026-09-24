from functools import lru_cache
from typing import Literal

from pydantic import PostgresDsn
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Camera Video Map API"
    ENVIRONMENT: Literal["development", "staging", "production"] = "development"
    DEBUG: bool = False

    DATABASE_URL: PostgresDsn
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10

    API_V1_PREFIX: str = "/api/v1"
    LOG_LEVEL: str = "INFO"
    DOCS_URL: str = "/docs"
    REDOC_URL: str = "/redoc"
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    SECRET_KEY: str
    ALGORITHM: Literal["HS256", "HS384", "HS512"] = "HS256"
    # API_KEY: str
    # API_KEY_HEADER: str = "X-API-Key"

    REDIS_URL: str = "redis://localhost:6379/0"
    CAMERA_GEOJSON_CACHE_TTL: int = 300

    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str
    MINIO_SECRET_KEY: str
    MINIO_SECURE: bool = False
    MINIO_BUCKET_VIDEOS: str = "videos"
    MINIO_BUCKET_FRAMES: str = "video-frames"

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore


settings = get_settings()
