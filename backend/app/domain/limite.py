"""Limite por categoria: situação do gasto no ciclo e quando avisar. Nada é guardado."""

from typing import Literal

Situacao = Literal["ok", "atencao", "estourado"]

_ORDEM: dict[str, int] = {"ok": 0, "atencao": 1, "estourado": 2}


def situacao(usado: int, limite: int) -> Situacao:
    """ok abaixo de 80%; atenção de 80% até 100% inclusive; estourado acima. Só inteiros."""
    if usado * 100 < limite * 80:
        return "ok"
    if usado <= limite:
        return "atencao"
    return "estourado"


def piorou(antes: Situacao, depois: Situacao) -> bool:
    """Avisa só quando a situação sobe de nível; repetir ou melhorar não avisa."""
    return _ORDEM[depois] > _ORDEM[antes]


def limite_permitido(tipo: str) -> bool:
    """Limite só faz sentido para o que sai."""
    return tipo == "saida"
