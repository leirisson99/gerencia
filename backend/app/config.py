from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str | None = None
    frontend_origin: str = "http://localhost:3000"
    cookie_secure: bool = True
    sessao_dias_inatividade: int = 30
    log_level: str = "INFO"

    @field_validator("database_url", "test_database_url")
    @classmethod
    def _driver_psycopg(cls, url: str | None) -> str | None:
        """Aceita postgres:// e postgresql:// (formato dos painéis de hospedagem) com psycopg 3."""
        if url is None:
            return url
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                return "postgresql+psycopg://" + url.removeprefix(prefixo)
        return url


@lru_cache
def get_settings() -> Settings:
    return Settings()
