"""Parcelas de dívidas: valores, datas e situação. Tudo em centavos."""

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date

from app.domain.recorrencia import data_prevista, no_mes


def dividir(valor_total: int, parcelas: int) -> list[int]:
    """`valor_total // parcelas` em cada uma; o resto dos centavos vai para a última."""
    if parcelas < 1 or valor_total < parcelas:
        raise ValueError("Cada parcela precisa de pelo menos 1 centavo.")
    base, resto = divmod(valor_total, parcelas)
    return [base] * (parcelas - 1) + [base + resto]


def datas_das_parcelas(dia_vencimento: int, inicio: date, parcelas: int) -> list[date]:
    """1ª na próxima ocorrência do dia a partir do início; as demais, mês a mês."""
    primeira = data_prevista(dia_vencimento, inicio)
    datas = []
    for k in range(parcelas):
        meses = primeira.month - 1 + k
        datas.append(no_mes(primeira.year + meses // 12, meses % 12 + 1, dia_vencimento))
    return datas


@dataclass(frozen=True)
class Situacao:
    pagas: int
    total: int
    valor_pago: int
    valor_restante: int
    quitada: bool


def situacao(parcelas: Iterable[tuple[int, bool]]) -> Situacao:
    """`parcelas`: (valor, paga) de cada parcela."""
    lista = list(parcelas)
    pago = sum(valor for valor, paga in lista if paga)
    pagas = sum(1 for _, paga in lista if paga)
    return Situacao(
        pagas=pagas,
        total=len(lista),
        valor_pago=pago,
        valor_restante=sum(valor for valor, _ in lista) - pago,
        quitada=pagas == len(lista),
    )
