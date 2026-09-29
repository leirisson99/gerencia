"""Ciclos derivados das datas dos salários. Nada aqui é guardado no banco."""

from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum


@dataclass(frozen=True)
class Ciclo:
    inicio: date
    fim: date | None  # None = ciclo aberto
    anterior: date | None  # início do ciclo anterior
    proximo: date | None  # início do próximo ciclo

    @property
    def aberto(self) -> bool:
        return self.fim is None


def _inicios(datas_salario: Iterable[date]) -> list[date]:
    # Salários na mesma data abrem um único ciclo.
    return sorted(set(datas_salario))


def _ciclo_na_posicao(inicios: list[date], i: int) -> Ciclo:
    proximo = inicios[i + 1] if i + 1 < len(inicios) else None
    return Ciclo(
        inicio=inicios[i],
        fim=proximo - timedelta(days=1) if proximo else None,
        anterior=inicios[i - 1] if i > 0 else None,
        proximo=proximo,
    )


def montar_ciclos(datas_salario: Iterable[date]) -> list[Ciclo]:
    inicios = _inicios(datas_salario)
    return [_ciclo_na_posicao(inicios, i) for i in range(len(inicios))]


def ciclo_da_data(datas_salario: Iterable[date], data: date) -> Ciclo | None:
    inicios = _inicios(datas_salario)
    posicao = bisect_right(inicios, data) - 1
    if posicao < 0:
        return None
    return _ciclo_na_posicao(inicios, posicao)


def ciclo_atual(datas_salario: Iterable[date]) -> Ciclo | None:
    inicios = _inicios(datas_salario)
    if not inicios:
        return None
    return _ciclo_na_posicao(inicios, len(inicios) - 1)


class ProblemaCobertura(Enum):
    SEM_SALARIO = "sem_salario"
    ANTES_DO_PRIMEIRO_CICLO = "antes_do_primeiro_ciclo"


def verificar_cobertura(
    datas_salario: Iterable[date], menor_data_outros: date | None
) -> ProblemaCobertura | None:
    """Todo lançamento que não é salário precisa cair num ciclo.

    `menor_data_outros` é a menor data entre os lançamentos que não são salário (None se não
    houver nenhum), já considerando a mudança que se quer gravar.
    """
    if menor_data_outros is None:
        return None
    datas = list(datas_salario)
    if not datas:
        return ProblemaCobertura.SEM_SALARIO
    if menor_data_outros < min(datas):
        return ProblemaCobertura.ANTES_DO_PRIMEIRO_CICLO
    return None
