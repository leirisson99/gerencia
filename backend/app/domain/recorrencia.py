"""Quando cai o previsto de uma recorrência dentro de um ciclo."""

from calendar import monthrange
from datetime import date


def _no_mes(ano: int, mes: int, dia: int) -> date:
    # Dia que não existe no mês (29–31) vira o último dia do mês.
    return date(ano, mes, min(dia, monthrange(ano, mes)[1]))


def data_prevista(dia: int, inicio_ciclo: date) -> date:
    """Próxima ocorrência do dia do mês a partir do início do ciclo (inclusive)."""
    candidato = _no_mes(inicio_ciclo.year, inicio_ciclo.month, dia)
    if candidato >= inicio_ciclo:
        return candidato
    if inicio_ciclo.month == 12:
        return _no_mes(inicio_ciclo.year + 1, 1, dia)
    return _no_mes(inicio_ciclo.year, inicio_ciclo.month + 1, dia)
