"""Regras puras dos lembretes: janela de vencimento e texto do resumo diário.

Contas a pagar e valores a receber são derivados dos lançamentos previstos, nunca guardados. O
resumo leva só contagens: nada de valores, descrições, categorias, nomes ou texto de lembretes.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Literal

JANELA_DIAS = 3

Situacao = Literal["atrasado", "a_vencer"]
Origem = Literal["conta", "valor", "livre"]

TITULO_RESUMO = "Gerencia"

# date.weekday(): segunda é 0.
_DIAS_DA_SEMANA = ("segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo")


def limite(hoje: date) -> date:
    """Último dia da janela "a vencer", inclusive."""
    return hoje + timedelta(days=JANELA_DIAS)


def situacao(data: date, hoje: date) -> Situacao | None:
    """Atrasado antes de hoje; a vencer de hoje até o limite; `None` fora da janela."""
    if data < hoje:
        return "atrasado"
    if data <= limite(hoje):
        return "a_vencer"
    return None


@dataclass(frozen=True)
class Total:
    atrasados: int = 0
    a_vencer: int = 0

    @property
    def soma(self) -> int:
        return self.atrasados + self.a_vencer


@dataclass(frozen=True)
class Contagem:
    contas: Total = field(default_factory=Total)
    valores: Total = field(default_factory=Total)
    livres: Total = field(default_factory=Total)

    @property
    def total(self) -> int:
        return self.contas.soma + self.valores.soma + self.livres.soma


def contar(itens: Iterable[tuple[Origem, Situacao]]) -> Contagem:
    """Conta atrasados e a vencer por origem."""
    somas = {origem: [0, 0] for origem in ("conta", "valor", "livre")}
    for origem, sit in itens:
        somas[origem][0 if sit == "atrasado" else 1] += 1
    return Contagem(
        contas=Total(*somas["conta"]),
        valores=Total(*somas["valor"]),
        livres=Total(*somas["livre"]),
    )


@dataclass(frozen=True)
class Mensagem:
    titulo: str
    corpo: str


def _plural(n: int, singular: str, plural: str) -> str:
    return singular if n == 1 else plural


def _parte(total: Total, nome: tuple[str, str], feminino: bool, dia: str) -> str | None:
    if total.soma == 0:
        return None
    base = f"{total.soma} {_plural(total.soma, *nome)}"
    atrasado = ("atrasada", "atrasadas") if feminino else ("atrasado", "atrasados")
    if total.a_vencer == 0:
        return f"{base}, {_plural(total.soma, *atrasado)}"
    if total.atrasados == 0:
        return f"{base} até {dia}"
    return f"{base} até {dia} ({total.atrasados} {_plural(total.atrasados, *atrasado)})"


def texto_resumo(contagem: Contagem, hoje: date) -> Mensagem | None:
    """Resumo do dia só com contagens; `None` quando não há nada a lembrar."""
    if contagem.total == 0:
        return None
    dia = _DIAS_DA_SEMANA[limite(hoje).weekday()]
    partes = [
        _parte(contagem.contas, ("conta a pagar", "contas a pagar"), True, dia),
        _parte(contagem.valores, ("valor a receber", "valores a receber"), False, dia),
        _parte(contagem.livres, ("lembrete", "lembretes"), False, dia),
    ]
    return Mensagem(titulo=TITULO_RESUMO, corpo=" · ".join(p for p in partes if p) + ".")
