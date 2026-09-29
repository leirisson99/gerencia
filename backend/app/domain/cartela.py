"""Cartela de poupança: casas base × 1…N mais uma casa de ajuste. Tudo em centavos."""

from collections.abc import Iterable
from dataclasses import dataclass
from math import isqrt


@dataclass(frozen=True)
class CasaGerada:
    ordem: int
    valor: int
    is_ajuste: bool


def _soma(base: int, n: int) -> int:
    return base * n * (n + 1) // 2


def _maior_n(meta: int, base: int) -> int:
    """Maior N com base × N(N+1)/2 ≤ meta."""
    n = (isqrt(8 * (meta // base) + 1) - 1) // 2
    while _soma(base, n + 1) <= meta:
        n += 1
    while _soma(base, n) > meta:
        n -= 1
    return n


def _validar(meta: int, base: int) -> None:
    if base <= 0 or meta < base:
        raise ValueError("A meta precisa ser maior ou igual ao valor base.")


def quantidade_de_casas(meta: int, base: int) -> int:
    _validar(meta, base)
    n = _maior_n(meta, base)
    return n + (1 if meta > _soma(base, n) else 0)


def gerar_casas(meta: int, base: int) -> list[CasaGerada]:
    """A soma das casas é sempre a meta; o resto vira a casa de ajuste."""
    _validar(meta, base)
    n = _maior_n(meta, base)
    casas = [CasaGerada(ordem=k, valor=base * k, is_ajuste=False) for k in range(1, n + 1)]
    resto = meta - _soma(base, n)
    if resto:
        casas.append(CasaGerada(ordem=n + 1, valor=resto, is_ajuste=True))
    return casas


@dataclass(frozen=True)
class Progresso:
    guardado: int
    falta: int
    percentual: int  # inteiro, arredondado para baixo
    maior_casa_livre: int | None


def progresso(casas: Iterable[tuple[int, bool]], meta: int) -> Progresso:
    """`casas`: (valor, depositada) de cada casa."""
    lista = list(casas)
    guardado = sum(valor for valor, depositada in lista if depositada)
    livres = [valor for valor, depositada in lista if not depositada]
    return Progresso(
        guardado=guardado,
        falta=meta - guardado,
        percentual=guardado * 100 // meta,
        maior_casa_livre=max(livres) if livres else None,
    )
