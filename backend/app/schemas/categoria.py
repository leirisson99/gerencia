from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.usuario import limpar_texto

MAX_NOME_CATEGORIA = 60


class CategoriaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nome: str
    tipo: Literal["entrada", "saida"]

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_NOME_CATEGORIA)


class CategoriaPatch(BaseModel):
    """Renomear e/ou ativar/desativar. O tipo não muda."""

    model_config = ConfigDict(extra="forbid")

    nome: str | None = None
    ativa: bool | None = None

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str | None) -> str:
        # Validadores só rodam para campos enviados; null explícito chega aqui como None.
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return limpar_texto(valor, MAX_NOME_CATEGORIA)

    @field_validator("ativa")
    @classmethod
    def _ativa(cls, valor: bool | None) -> bool:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor


class CategoriaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    nome: str
    tipo: str
    sistema: bool
    ativa: bool
