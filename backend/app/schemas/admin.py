from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.usuario import DadosPessoaisIn


class DadosAdmin(DadosPessoaisIn):
    """Dados do comando criar-admin; a senha é sempre gerada."""


class UsuarioAdminOut(BaseModel):
    """O administrador vê só isto de cada conta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    criado_em: datetime


class SenhaTemporariaOut(BaseModel):
    senha_temporaria: str
