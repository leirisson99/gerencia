"""Ciclos derivados das datas dos salários ou do mês do calendário. Nada é guardado no banco."""

import calendar
from bisect import bisect_right
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import date, timedelta
from enum import Enum

from app.domain.usuario import ciclo_pelo_mes


@dataclass(frozen=True)
class Ciclo:
    inicio: date
    fim: date | None  # None = ciclo aberto
    anterior: date | None  # início do ciclo anterior
    proximo: date | None  # início do próximo ciclo
    mes_atual: bool = False  # ciclo mensal que contém hoje

    @property
    def aberto(self) -> bool:
        return self.fim is None or self.mes_atual


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


def _mes_seguinte(inicio: date) -> date:
    return (
        date(inicio.year + 1, 1, 1)
        if inicio.month == 12
        else inicio.replace(month=inicio.month + 1)
    )


def _mes_anterior(inicio: date) -> date:
    return (
        date(inicio.year - 1, 12, 1)
        if inicio.month == 1
        else inicio.replace(month=inicio.month - 1)
    )


def ciclo_mensal(data: date, hoje: date, primeira_data: date | None) -> Ciclo:
    """Ciclo do prestador: o mês do calendário que contém `data`.

    `primeira_data` é a data do lançamento mais antigo do usuário (None sem lançamentos): só há
    anterior se existir lançamento antes do mês. Não há próximo depois do mês de hoje.
    """
    inicio = data.replace(day=1)
    ultimo_dia = calendar.monthrange(data.year, data.month)[1]
    mes_de_hoje = hoje.replace(day=1)
    seguinte = _mes_seguinte(inicio)
    return Ciclo(
        inicio=inicio,
        fim=data.replace(day=ultimo_dia),
        anterior=(
            _mes_anterior(inicio) if primeira_data is not None and primeira_data < inicio else None
        ),
        proximo=seguinte if seguinte <= mes_de_hoje else None,
        mes_atual=inicio == mes_de_hoje,
    )


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


class ProblemaTroca(Enum):
    SALARIO_INVALIDO = "salario_invalido"
    LANCAMENTOS_SEM_CICLO = "lancamentos_sem_ciclo"


def verificar_troca_tipo_renda(
    atual: str,
    novo: str,
    datas_salario: Iterable[date],
    menor_data_outros: date | None,
    salario_irregular: bool,
) -> ProblemaTroca | None:
    """Só a troca do ciclo pelo mês para o ciclo pelo salário pode deixar algo fora de ciclo.

    `datas_salario` são os salários realizados; `menor_data_outros` é a menor data entre os outros
    lançamentos; `salario_irregular` indica "Salário" previsto ou com data futura, que o ciclo pelo
    salário não aceita.
    """
    if not ciclo_pelo_mes(atual) or ciclo_pelo_mes(novo):
        return None
    if salario_irregular:
        return ProblemaTroca.SALARIO_INVALIDO
    if verificar_cobertura(datas_salario, menor_data_outros):
        return ProblemaTroca.LANCAMENTOS_SEM_CICLO
    return None
