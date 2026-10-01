from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.domain.lembrete import Origem, Situacao
from app.schemas.lancamento import LancamentoOut


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
