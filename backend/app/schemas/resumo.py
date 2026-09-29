from pydantic import BaseModel

from app.domain.limite import Situacao
from app.schemas.ciclo import CicloOut


class TotalCategoriaOut(BaseModel):
    """`limite` e `situacao` só em saídas com limite; nos demais, `null`."""

    categoria_id: int
    nome: str
    total: int  # centavos
    limite: int | None = None
    situacao: Situacao | None = None


class ResumoCicloOut(BaseModel):
    """Só lançamentos realizados que contam no saldo. Listas por total decrescente e nome."""

    ciclo: CicloOut
    entradas: int
    saidas: int
    saldo: int
    saidas_por_categoria: list[TotalCategoriaOut]
    entradas_por_categoria: list[TotalCategoriaOut]
