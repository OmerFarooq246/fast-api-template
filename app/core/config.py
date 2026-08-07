from enum import StrEnum
from functools import lru_cache
from typing import Self

from pydantic import AnyHttpUrl, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url

DEVELOPMENT_SECRET = "development-only-change-me"  # noqa: S105


class Environment(StrEnum):
    LOCAL = "local"
    TEST = "test"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables and an optional .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    environment: Environment = Environment.LOCAL
    project_name: str = "fast-api-template"
    version: str = "v1"
    debug: bool = False
    cors_origins: list[AnyHttpUrl] = [AnyHttpUrl("http://localhost:3000")]

    database_uri: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fast_api_template"
    secret_key: SecretStr = SecretStr(DEVELOPMENT_SECRET)
    algorithm: str = "HS256"
    access_token_expire_minutes: int = Field(default=30, gt=0)

    @field_validator("database_uri")
    @classmethod
    def validate_async_database_uri(cls, value: str) -> str:
        url = make_url(value)
        if url.drivername != "postgresql+asyncpg":
            raise ValueError("DATABASE_URI must use the postgresql+asyncpg driver")
        if not url.database:
            raise ValueError("DATABASE_URI must include a database name")
        return value

    @model_validator(mode="after")
    def validate_deployment_secrets(self) -> Self:
        if self.environment in {Environment.STAGING, Environment.PRODUCTION}:
            secret = self.secret_key.get_secret_value()
            if secret == DEVELOPMENT_SECRET or len(secret) < 32:
                raise ValueError(
                    "SECRET_KEY must be changed and contain at least 32 characters "
                    "in staging and production"
                )
        return self

    @property
    def cors_origin_strings(self) -> list[str]:
        return [str(origin).rstrip("/") for origin in self.cors_origins]


@lru_cache
def get_settings() -> Settings:
    return Settings()
