"""Saldo e totais por categoria de um conjunto de lançamentos. Nada é guardado."""

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Movimento:
    categoria_id: int
    tipo: str  # "entrada" | "saida"
    valor: int  # centavos
    status: str  # "previsto" | "realizado"
    conta_no_saldo: bool


@dataclass(frozen=True)
class Resumo:
    entradas: int
    saidas: int
    saldo: int
    por_categoria: dict[int, int]  # categoria_id → total em centavos


def conta_no_resumo(movimento: Movimento) -> bool:
    """Só o que aconteceu e não é contado em outro lugar (ex.: parcela paga no cartão)."""
    return movimento.status == "realizado" and movimento.conta_no_saldo


def resumir(movimentos: Iterable[Movimento]) -> Resumo:
    totais: dict[str, int] = {"entrada": 0, "saida": 0}
    por_categoria: defaultdict[int, int] = defaultdict(int)
    for movimento in movimentos:
        if not conta_no_resumo(movimento):
            continue
        totais[movimento.tipo] += movimento.valor
        por_categoria[movimento.categoria_id] += movimento.valor
    return Resumo(
        entradas=totais["entrada"],
        saidas=totais["saida"],
        saldo=totais["entrada"] - totais["saida"],
        por_categoria=dict(por_categoria),
    )
