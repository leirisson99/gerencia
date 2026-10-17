"""Contas compartilhadas: rateio da cobrança, status da cota e prazo do convite. Centavos."""

from collections.abc import Sequence
from datetime import date, datetime, timedelta
from typing import Literal

from app.domain.parcelas import dividir
from app.domain.recorrencia import no_mes

MAX_PARTICIPANTES = 20
PRAZO_CONVITE = timedelta(days=30)
TOTAL_BPS = 10_000

Modo = Literal["igual", "percentual", "fixo"]
StatusCota = Literal["pendente", "informado", "confirmado"]


class DivisaoInvalida(ValueError):
    """A cobrança não fecha. `diferenca` é o que falta (positivo) ou sobra (negativo)."""

    def __init__(self, mensagem: str, diferenca: int = 0) -> None:
        super().__init__(mensagem)
        self.diferenca = diferenca


def ratear(total: int, modo: str, valores: Sequence[int | None]) -> list[int]:
    """Cota de cada participante aceito, na ordem de `valores`; a soma é sempre `total`.

    `valores`: um item por participante. Em `igual` é ignorado; em `percentual` são pontos-base
    (soma 10000); em `fixo` são centavos (soma igual ao total).
    """
    n = len(valores)
    if n < 1 or n > MAX_PARTICIPANTES:
        raise DivisaoInvalida(f"Uma conta tem de 1 a {MAX_PARTICIPANTES} participantes.")
    if total < 1:
        raise DivisaoInvalida("O total precisa ser maior que zero.")
    if modo == "igual":
        if total < n:
            raise DivisaoInvalida("Cada participante precisa de pelo menos 1 centavo.")
        return dividir(total, n)
    if modo not in ("percentual", "fixo"):
        raise DivisaoInvalida("Modo de divisão desconhecido.")
    if any(v is None or v < 0 for v in valores):
        raise DivisaoInvalida("Informe o valor de cada participante.")
    definidos = [int(v) for v in valores if v is not None]
    if modo == "fixo":
        diferenca = total - sum(definidos)
        if diferenca != 0:
            raise DivisaoInvalida("Os valores fixos precisam somar o total.", diferenca)
        cotas = definidos
    else:
        diferenca = TOTAL_BPS - sum(definidos)
        if diferenca != 0:
            raise DivisaoInvalida("Os percentuais precisam somar 100%.", diferenca)
        cotas = [total * bps // TOTAL_BPS for bps in definidos]
        cotas[-1] += total - sum(cotas)
    if min(cotas) < 1:
        raise DivisaoInvalida("Cada participante precisa de pelo menos 1 centavo.")
    return cotas


def status_da_cota(lancamento_status: str | None, confirmado_em: datetime | None) -> StatusCota:
    """Derivado do lançamento do titular e da confirmação do dono; nunca armazenado."""
    if lancamento_status != "realizado":
        return "pendente"
    return "confirmado" if confirmado_em is not None else "informado"


def convite_expirado(convidado_em: datetime, agora: datetime) -> bool:
    return agora - convidado_em > PRAZO_CONVITE


def data_da_cota(competencia: date, dia_vencimento: int) -> date:
    """Vencimento no mês da competência; dia 29–31 que não existe vira o último dia do mês."""
    return no_mes(competencia.year, competencia.month, dia_vencimento)
