from datetime import date

from pydantic import BaseModel, ConfigDict, StrictInt, field_validator

from app.schemas.lancamento import limpar_descricao


class RetiradaIn(BaseModel):
    """Valor e data obrigatórios; a validação de valor e data fica no domínio."""

    model_config = ConfigDict(extra="forbid")

    valor: StrictInt
    data: date
    descricao: str | None = None

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return limpar_descricao(valor)


class RetiradaPatch(BaseModel):
    """Edição parcial; muda os dois lados juntos. `descricao: null` remove a descrição."""

    model_config = ConfigDict(extra="forbid")

    valor: StrictInt | None = None
    data: date | None = None
    descricao: str | None = None

    @field_validator("valor", "data")
    @classmethod
    def _sem_null(cls, valor: object) -> object:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return limpar_descricao(valor)


class RetiradaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    data: date
    valor: int  # centavos
    descricao: str | None
    lancamento_pj_id: int
    lancamento_pf_id: int
