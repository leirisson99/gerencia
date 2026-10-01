from functools import lru_cache
from typing import Self

from argon2 import extract_parameters
from argon2.exceptions import InvalidHashError
from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.schemas.admin import DadosAdmin


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    test_database_url: str | None = None
    frontend_origin: str = "http://localhost:3000"
    cookie_secure: bool = True
    sessao_dias_inatividade: int = 30
    log_level: str = "INFO"
    # Administrador único, sincronizado a cada inicialização: o .env sempre vence.
    admin_nome: str = "Administrador"
    admin_email: str | None = None
    admin_senha_hash: str | None = None

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

    @model_validator(mode="after")
    def _admin_completo(self) -> Self:
        if (self.admin_email is None) != (self.admin_senha_hash is None):
            raise ValueError("Defina ADMIN_EMAIL e ADMIN_SENHA_HASH juntos, ou nenhum dos dois.")
        if self.admin_senha_hash is not None:
            try:
                extract_parameters(self.admin_senha_hash)
            except InvalidHashError:
                raise ValueError(
                    "ADMIN_SENHA_HASH não é um hash argon2. "
                    "Gere com: uv run python -m app.cli hash-senha"
                ) from None
        return self

    def admin(self) -> DadosAdmin | None:
        if self.admin_email is None or self.admin_senha_hash is None:
            return None
        return DadosAdmin(
            nome=self.admin_nome, email=self.admin_email, senha_hash=self.admin_senha_hash
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
