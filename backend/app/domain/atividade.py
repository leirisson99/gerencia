"""Regras puras da atividade de uma conta: visita auditada, retenção e paginação."""

from datetime import datetime, timedelta
from typing import Literal

JANELA_VISITA = timedelta(minutes=30)
MESES_RETENCAO = 12
EVENTOS_POR_PAGINA = 50


def precisa_registrar_visita(ultima: datetime | None, agora: datetime) -> bool:
    """Uma visita do administrador à mesma conta vale por 30 minutos."""
    return ultima is None or agora - ultima >= JANELA_VISITA


def limite_retencao(agora: datetime) -> datetime:
    """Mesmo dia e hora, 12 meses antes; 29/02 sem par vira 28/02."""
    ano = agora.year - MESES_RETENCAO // 12
    try:
        return agora.replace(year=ano)
    except ValueError:
        return agora.replace(year=ano, day=28)


def tipo_edicao_lembrete(
    concluido_antes: bool, concluido_depois: bool
) -> Literal["lembrete_concluido", "lembrete_editado"]:
    """Concluir vale mais que editar: uma edição que conclui é só `lembrete_concluido`."""
    if concluido_depois and not concluido_antes:
        return "lembrete_concluido"
    return "lembrete_editado"


def fatiar_pagina[T](itens: list[T], limite: int) -> tuple[list[T], bool]:
    """Recebe até `limite + 1` itens; devolve os `limite` primeiros e se há mais."""
    return itens[:limite], len(itens) > limite
