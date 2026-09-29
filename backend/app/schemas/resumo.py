from pydantic import BaseModel

from app.schemas.ciclo import CicloOut


class TotalCategoriaOut(BaseModel):
    categoria_id: int
    nome: str
    total: int  # centavos


class ResumoCicloOut(BaseModel):
    """Só lançamentos realizados que contam no saldo. Listas por total decrescente e nome."""

    ciclo: CicloOut
    entradas: int
    saidas: int
    saldo: int
    saidas_por_categoria: list[TotalCategoriaOut]
    entradas_por_categoria: list[TotalCategoriaOut]
