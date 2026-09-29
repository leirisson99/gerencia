from datetime import date

import pytest

from app.domain.recorrencia import data_prevista


@pytest.mark.parametrize(
    ("dia", "inicio", "esperado"),
    [
        (10, date(2026, 10, 5), date(2026, 10, 10)),  # ainda neste mês
        (5, date(2026, 10, 5), date(2026, 10, 5)),  # no próprio dia do início
        (1, date(2026, 10, 5), date(2026, 11, 1)),  # já passou: mês seguinte
        (4, date(2026, 10, 5), date(2026, 11, 4)),
        (31, date(2026, 4, 10), date(2026, 4, 30)),  # abril tem 30 dias
        (31, date(2026, 2, 3), date(2026, 2, 28)),  # fevereiro comum
        (30, date(2028, 2, 3), date(2028, 2, 29)),  # fevereiro bissexto
        (30, date(2026, 1, 31), date(2026, 2, 28)),  # passou em janeiro, limita em fevereiro
        (5, date(2026, 12, 20), date(2027, 1, 5)),  # virada de ano
        (31, date(2026, 12, 31), date(2026, 12, 31)),
    ],
)
def test_proxima_ocorrencia_a_partir_do_inicio(dia: int, inicio: date, esperado: date) -> None:
    assert data_prevista(dia, inicio) == esperado


@pytest.mark.parametrize("dia", range(1, 32))
def test_nunca_antes_do_inicio_nem_mais_de_um_mes_depois(dia: int) -> None:
    for mes in range(1, 13):
        inicio = date(2026, mes, 15)
        prevista = data_prevista(dia, inicio)
        assert inicio <= prevista
        assert (prevista - inicio).days < 32
