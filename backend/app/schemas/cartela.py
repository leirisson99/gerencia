from datetime import date

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.usuario import limpar_texto
from app.schemas.lancamento import Valor

MAX_NOME_CARTELA = 80
BASE_PADRAO = 100  # R$ 1,00


class CartelaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str
    meta: Valor
    valor_base: Valor = BASE_PADRAO

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_NOME_CARTELA)


class CasaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ordem: int
    valor: int
    is_ajuste: bool
    depositado_em: date | None
    lancamento_id: int | None


class CartelaOut(BaseModel):
    id: int
    nome: str
    meta: int
    valor_base: int
    guardado: int
    falta: int
    percentual: int
    maior_casa_livre: int | None
    casas: list[CasaOut]
