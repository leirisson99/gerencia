"""Regras puras do serviço a receber. A situação é derivada, nunca guardada."""

from datetime import date
from typing import Literal

SituacaoServico = Literal["a_receber", "atrasado", "recebido"]

MAX_DESCRICAO_LANCAMENTO = 200


def situacao(status_lancamento: str, data_prevista: date, hoje: date) -> SituacaoServico:
    """Recebido se a entrada foi realizada; senão atrasado a partir do dia seguinte ao previsto."""
    if status_lancamento == "realizado":
        return "recebido"
    return "atrasado" if data_prevista < hoje else "a_receber"


def descricao_do_lancamento(cliente: str, descricao: str | None) -> str:
    """Descrição da entrada gerada: o cliente, e a descrição do serviço quando houver."""
    texto = f"{cliente} — {descricao}" if descricao else cliente
    return texto[:MAX_DESCRICAO_LANCAMENTO]
