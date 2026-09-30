from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, StrictInt, field_validator

from app.domain.servico import SituacaoServico
from app.domain.usuario import limpar_texto
from app.schemas.lancamento import Valor, limpar_descricao

MAX_CLIENTE = 120


class ServicoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cliente: str
    descricao: str | None = None
    valor: Valor
    data_prevista: date
    categoria_id: StrictInt

    @field_validator("cliente")
    @classmethod
    def _cliente(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_CLIENTE)

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return limpar_descricao(valor)


class ServicoPatch(BaseModel):
    """Edição parcial, só enquanto não recebido. `descricao: null` remove a descrição."""

    model_config = ConfigDict(extra="forbid")

    cliente: str | None = None
    descricao: str | None = None
    valor: Valor | None = None
    data_prevista: date | None = None
    categoria_id: StrictInt | None = None

    @field_validator("cliente")
    @classmethod
    def _cliente(cls, valor: str | None) -> str:
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return limpar_texto(valor, MAX_CLIENTE)

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str | None) -> str | None:
        return limpar_descricao(valor)

    @field_validator("valor", "data_prevista", "categoria_id")
    @classmethod
    def _sem_null(cls, valor: object) -> object:
        # Validadores só rodam para campos enviados; null explícito chega aqui como None.
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor


class RecebimentoIn(BaseModel):
    """`valor` ausente: recebeu o valor combinado."""

    model_config = ConfigDict(extra="forbid")

    data: date
    valor: Valor | None = None


class ServicoOut(BaseModel):
    id: int
    cliente: str
    descricao: str | None
    valor: int  # centavos, o combinado
    data_prevista: date
    categoria_id: int
    lancamento_id: int
    situacao: SituacaoServico
    data_recebimento: date | None
    valor_recebido: int | None
    criado_em: datetime
