from datetime import date
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator

from app.domain.usuario import limpar_texto
from app.schemas.lancamento import MAX_DESCRICAO, LancamentoOut, Valor
from app.schemas.recorrencia import Dia

MAX_PESSOA = 120
MAX_PARCELAS = 120


class DividaIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    descricao: str
    pessoa: str
    direcao: Literal["devo", "me_devem"]
    valor_total: Valor
    parcelas: Annotated[StrictInt, Field(ge=1, le=MAX_PARCELAS)]
    forma_pagamento: Literal["pix", "boleto", "cartao", "dinheiro"]
    dia_vencimento: Dia
    data_inicio: date
    categoria_id: StrictInt

    @field_validator("descricao")
    @classmethod
    def _descricao(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_DESCRICAO)

    @field_validator("pessoa")
    @classmethod
    def _pessoa(cls, valor: str) -> str:
        return limpar_texto(valor, MAX_PESSOA)


class DividaOut(BaseModel):
    id: int
    descricao: str
    pessoa: str
    direcao: str
    valor_total: int
    parcelas: int
    forma_pagamento: str
    dia_vencimento: int
    data_inicio: date
    categoria_id: int
    parcelas_pagas: int
    valor_pago: int
    valor_restante: int
    quitada: bool
    lancamentos: list[LancamentoOut]
