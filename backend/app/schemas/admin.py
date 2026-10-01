from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.usuario import MAX_NOME, limpar_texto, normalizar_email

SituacaoConta = Literal["ativos", "desativados"]


class DadosAdmin(BaseModel):
    """O administrador como vem do .env (ADMIN_NOME, ADMIN_EMAIL, ADMIN_SENHA_HASH)."""

    nome: str
    email: str
    senha_hash: str

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_NOME)

    @field_validator("email")
    @classmethod
    def _email(cls, valor: str) -> str:
        return normalizar_email(valor)


class UsuarioAdminOut(BaseModel):
    """O administrador vê só isto de cada conta."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    email: str
    criado_em: datetime
    ativo: bool


class SenhaTemporariaOut(BaseModel):
    senha_temporaria: str


class ContasOut(BaseModel):
    total: int
    ativas: int
    desativadas: int


class LancamentosOut(BaseModel):
    total: int
    realizados: int
    previstos: int


class MesOut(BaseModel):
    mes: str  # AAAA-MM
    entradas: int
    saidas: int


class FormaOut(BaseModel):
    forma: Literal["pix", "boleto", "cartao", "dinheiro"]
    quantidade: int


class ResumoAdminOut(BaseModel):
    """Só contagens somadas entre todos os usuários: nenhum valor, nenhum usuário."""

    contas: ContasOut
    lancamentos: LancamentosOut
    por_mes: list[MesOut]
    dividas_por_forma: list[FormaOut]
