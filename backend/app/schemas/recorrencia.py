from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from app.domain.usuario import limpar_texto
from app.schemas.lancamento import MAX_DESCRICAO, Valor

Dia = Annotated[StrictInt, Field(ge=1, le=31)]


class RecorrenciaIn(BaseModel):
    """O tipo vem da categoria; "Salário" não é aceita."""

    model_config = ConfigDict(extra="forbid")

    descricao: str
    valor: Valor
    categoria_id: StrictInt
    dia: Dia

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_DESCRICAO)


class RecorrenciaPatch(BaseModel):
    """Vale para os próximos ciclos. Nenhum campo aceita null."""

    model_config = ConfigDict(extra="forbid")

    descricao: str | None = None
    valor: Valor | None = None
    categoria_id: StrictInt | None = None
    dia: Dia | None = None
    ativa: bool | None = None

    @field_validator("descricao", "valor", "categoria_id", "dia", "ativa")
    @classmethod
    def _sem_null(cls, valor: object) -> object:
        # Validadores só rodam para campos enviados; null explícito chega aqui como None.
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_DESCRICAO)


class RecorrenciaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    descricao: str
    valor: int
    tipo: str
    categoria_id: int
    dia: int
    ativa: bool
