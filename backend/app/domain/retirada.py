"""Regras puras da retirada: dinheiro que sai da PJ e entra na PF, sempre em par."""

from dataclasses import dataclass
from datetime import date

from app.domain.usuario import Carteira


@dataclass(frozen=True)
class Lado:
    carteira: Carteira
    tipo: str  # "entrada" | "saida"
    valor: int  # centavos
    data: date


def validar_retirada(valor: int, data: date, hoje: date) -> dict[str, str]:
    """Problemas por campo; vazio quando a retirada pode ser gravada."""
    erros: dict[str, str] = {}
    if valor <= 0:
        erros["valor"] = "O valor da retirada deve ser maior que zero."
    if data > hoje:
        erros["data"] = "A retirada é registrada quando acontece; a data não pode ser futura."
    return erros


def lados_da_retirada(valor: int, data: date) -> tuple[Lado, Lado]:
    """Saída na PJ e entrada na PF, de mesmo valor e data (constituição 7.0.0, princípio I)."""
    return (
        Lado(carteira="pj", tipo="saida", valor=valor, data=data),
        Lado(carteira="pf", tipo="entrada", valor=valor, data=data),
    )
