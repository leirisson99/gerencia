from functools import lru_cache

from argon2 import extract_parameters
from argon2.exceptions import InvalidHashError
from pydantic import field_validator
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
    # Push (Web Push/VAPID). Sem as chaves, as notificações ficam desligadas.
    vapid_chave_publica: str | None = None
    vapid_chave_privada: str | None = None
    vapid_contato: str | None = None
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

    @field_validator("admin_email", "admin_senha_hash", mode="before")
    @classmethod
    def _sem_aspas(cls, valor: str | None) -> str | None:
        """Painéis de hospedagem passam o valor como foi colado: tira espaços e aspas em volta."""
        if valor is None:
            return None
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in "'\"":
            valor = valor[1:-1].strip()
        return valor or None

    def problema_admin(self) -> str | None:
        """Por que o admin do .env ficou desligado, sem repetir o valor (vai para o log)."""
        if self.admin_email is None and self.admin_senha_hash is None:
            return None
        if self.admin_email is None or self.admin_senha_hash is None:
            return "defina ADMIN_EMAIL e ADMIN_SENHA_HASH juntos, ou nenhum dos dois."
        try:
            extract_parameters(self.admin_senha_hash)
        except InvalidHashError:
            return (
                "ADMIN_SENHA_HASH não é um hash argon2 válido (veio cortado ou com outro "
                "conteúdo). Gere com: uv run python -m app.cli hash-senha"
            )
        return None

    def admin(self) -> DadosAdmin | None:
        """O admin do .env, ou None quando não configurado ou com problema."""
        if self.problema_admin() is not None:
            return None
        if self.admin_email is None or self.admin_senha_hash is None:
            return None
        return DadosAdmin(
            nome=self.admin_nome, email=self.admin_email, senha_hash=self.admin_senha_hash
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()
