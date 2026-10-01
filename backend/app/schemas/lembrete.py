from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.domain.lembrete import Origem, Situacao
from app.domain.usuario import limpar_texto
from app.schemas.lancamento import LancamentoOut

MAX_TEXTO = 200


class LembreteLivreIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    texto: str
    data: date

    @field_validator("texto")
    @classmethod
    def _texto(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_TEXTO)


class LembreteLivrePatch(BaseModel):
    """Edição parcial; `concluido` marca ou desfaz a conclusão. `null` não é aceito."""

    model_config = ConfigDict(extra="forbid")

    texto: str | None = None
    data: date | None = None
    concluido: bool | None = None

    @field_validator("texto", "data", "concluido", mode="before")
    @classmethod
    def _sem_null(cls, valor: object) -> object:
        # Validadores só rodam para campos enviados; null explícito chega aqui como None.
        if valor is None:
            raise ValueError("Campo obrigatório.")
        return valor

    @field_validator("texto")
    @classmethod
    def _texto(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_TEXTO)


class LembreteLivreOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    texto: str
    data: date
    concluido: bool
    concluido_em: datetime | None
    criado_em: datetime


class ItemLembrete(BaseModel):
    """Um lançamento previsto (conta ou valor) ou um lembrete livre, na janela."""

    origem: Origem
    situacao: Situacao
    data: date
    lancamento: LancamentoOut | None = None  # em "conta" e "valor"
    lembrete: LembreteLivreOut | None = None  # em "livre"


class LembretesOut(BaseModel):
    """Derivado na hora: nada aqui é guardado, exceto os lembretes livres."""

    hoje: date
    limite: date
    atrasados: list[ItemLembrete]
    a_vencer: list[ItemLembrete]
