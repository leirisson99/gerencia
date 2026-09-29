"""Regras puras de login e sessão. Toda hora chega por parâmetro."""

from datetime import datetime, timedelta

MAX_FALHAS = 5
JANELA_FALHAS = timedelta(minutes=15)
DURACAO_BLOQUEIO = timedelta(minutes=15)


def sessao_expirada(ultimo_uso_em: datetime, agora: datetime, dias: int = 30) -> bool:
    return agora - ultimo_uso_em >= timedelta(days=dias)


def calcular_bloqueio(falhas: list[datetime], agora: datetime) -> datetime | None:
    """Devolve até quando o login está bloqueado, ou None se estiver liberado.

    `falhas` são as falhas desde o último login bem-sucedido. MAX_FALHAS falhas dentro de
    JANELA_FALHAS bloqueiam por DURACAO_BLOQUEIO a partir da última delas. Falhas anteriores
    ao fim de um bloqueio deixam de contar.
    """
    bloqueado_ate: datetime | None = None
    janela: list[datetime] = []
    for falha in sorted(falhas):
        if bloqueado_ate is not None:
            if falha < bloqueado_ate:
                continue
            bloqueado_ate = None
        janela = [f for f in janela if falha - f < JANELA_FALHAS]
        janela.append(falha)
        if len(janela) >= MAX_FALHAS:
            bloqueado_ate = falha + DURACAO_BLOQUEIO
            janela = []

    if bloqueado_ate is not None and agora < bloqueado_ate:
        return bloqueado_ate
    return None
