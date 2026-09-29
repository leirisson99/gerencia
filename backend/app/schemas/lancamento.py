from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

VALOR_MAXIMO = 99_999_999_999  # R$ 999.999.999,99
MAX_DESCRICAO = 200

# Centavos, sempre inteiro: 10.5, "1000" e true são recusados.
Valor = Annotated[StrictInt, Field(gt=0, le=VALOR_MAXIMO)]
Status = Literal["previsto", "realizado"]


def _limpar_descricao(valor: str | None) -> str | None:
    if valor is None:
        return None
    texto = valor.strip()
    if len(texto) > MAX_DESCRICAO:
        raise ValueError(f"Máximo de {MAX_DESCRICAO} caracteres.")
    return texto or None


class LancamentoIn(BaseModel):
    """Só valor, categoria e data são obrigatórios. O tipo vem da categoria."""

    model_config = ConfigDict(extra="forbid")

    valor: Valor
    categoria_id: StrictInt
    data: date
    descricao: str | None = None
    status: Status = "realizado"

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return _limpar_descricao(valor)


class LancamentoPatch(BaseModel):
    """Edição parcial. `descricao: null` remove a descrição; os demais não aceitam null."""

    model_config = ConfigDict(extra="forbid")

    valor: Valor | None = None
    categoria_id: StrictInt | None = None
    data: date | None = None
    descricao: str | None = None
    status: Status | None = None

    @field_validator("valor", "categoria_id", "data", "status")
    @classmethod
    def _sem_null(cls, valor: object) -> object:
        # Validadores só rodam para campos enviados; null explícito chega aqui como None.
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return _limpar_descricao(valor)


class LancamentoOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    valor: int
    tipo: str
    categoria_id: int
    data: date
    descricao: str | None
    status: str
    conta_no_saldo: bool
    abre_ciclo: bool
    criado_em: datetime
