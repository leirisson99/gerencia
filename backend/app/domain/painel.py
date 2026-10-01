"""Regras puras do resumo do administrador: só contagens, nunca valores."""

from collections.abc import Mapping
from datetime import date

FORMAS_PAGAMENTO = ("pix", "boleto", "cartao", "dinheiro")


def ultimos_meses(hoje: date, quantidade: int) -> list[date]:
    """Primeiro dia de cada um dos últimos `quantidade` meses, do mais antigo ao atual."""
    indice_atual = hoje.year * 12 + hoje.month - 1
    return [
        date(indice // 12, indice % 12 + 1, 1)
        for indice in range(indice_atual - quantidade + 1, indice_atual + 1)
    ]


def serie_mensal(
    contagens: Mapping[tuple[date, str], int], meses: list[date]
) -> list[tuple[date, int, int]]:
    """(mês, entradas, saídas) para cada mês da janela; mês sem movimento vem com zero."""
    return [
        (mes, contagens.get((mes, "entrada"), 0), contagens.get((mes, "saida"), 0)) for mes in meses
    ]


def ranking_formas(contagens: Mapping[str, int]) -> list[tuple[str, int]]:
    """Todas as formas de pagamento, da mais usada à menos; empate segue a ordem fixa."""
    return sorted(
        ((forma, contagens.get(forma, 0)) for forma in FORMAS_PAGAMENTO),
        key=lambda item: -item[1],
    )
