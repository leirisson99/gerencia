"""Texto de extrato → centavos e datas. Dinheiro só em `int`: nunca float nem Decimal."""

import re
import unicodedata
from datetime import date

from app.domain.extrato import ErroExtrato

_SINAIS = "+-−"
_MESES = {
    "janeiro": 1, "fevereiro": 2, "marco": 3, "abril": 4, "maio": 5, "junho": 6,
    "julho": 7, "agosto": 8, "setembro": 9, "outubro": 10, "novembro": 11, "dezembro": 12,
}  # fmt: skip
_MESES_ABREV = {nome[:3]: numero for nome, numero in _MESES.items()}

FORMATOS_DATA = {
    "dd/mm/aaaa": re.compile(r"(?P<d>\d{1,2})/(?P<m>\d{1,2})/(?P<a>\d{4})"),
    "dd-mm-aaaa": re.compile(r"(?P<d>\d{1,2})-(?P<m>\d{1,2})-(?P<a>\d{4})"),
    "aaaa-mm-dd": re.compile(r"(?P<a>\d{4})-(?P<m>\d{1,2})-(?P<d>\d{1,2})"),
    "mm/dd/aaaa": re.compile(r"(?P<m>\d{1,2})/(?P<d>\d{1,2})/(?P<a>\d{4})"),
}
# Tentados em ordem quando o formato não é informado (padrão brasileiro primeiro).
_AUTOMATICOS = ("dd/mm/aaaa", "dd-mm-aaaa", "aaaa-mm-dd")
_COMPACTA = re.compile(r"(?P<a>\d{4})(?P<m>\d{2})(?P<d>\d{2})(?:\d{6})?(?:\.\d+)?(?:\[.*\])?")
_EXTENSO = re.compile(r"(?P<d>\d{1,2})\s+(?:de\s+)?(?P<mes>[a-z]+)\.?\s+(?:de\s+)?(?P<a>\d{4})")


def _sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _milhar_valido(inteiro: str, separador: str | None) -> str:
    """Remove o separador de milhar, exigindo grupos de 3 dígitos."""
    if separador and separador in inteiro:
        if not re.fullmatch(rf"\d{{1,3}}(?:{re.escape(separador)}\d{{3}})+", inteiro):
            raise ErroExtrato("Valor inválido no extrato.")
        return inteiro.replace(separador, "")
    if not inteiro.isdigit():
        raise ErroExtrato("Valor inválido no extrato.")
    return inteiro


def centavos(texto: str, decimal: str | None = None) -> int:
    """'-R$ 1.234,56' → -123456. Sem `decimal`, o separador seguido de 2 dígitos é o decimal."""
    bruto = texto.replace("R$", "").replace(" ", "").strip()
    negativo = "-" in bruto or "−" in bruto
    numero = bruto.strip(_SINAIS)
    if not numero or not re.fullmatch(r"[\d.,]+", numero):
        raise ErroExtrato("Valor inválido no extrato.")

    if decimal is None:
        ultimo = max(numero.rfind(","), numero.rfind("."))
        casas = len(numero) - ultimo - 1
        if ultimo == -1:
            decimal = None
        elif casas == 2:
            decimal = numero[ultimo]
        elif casas == 3:
            decimal = None  # só milhar: "1.234"
        else:
            raise ErroExtrato("Valor inválido no extrato.")

    if decimal is None:
        milhar = "." if "." in numero else ("," if "," in numero else None)
        if milhar and ("," in numero and "." in numero):
            raise ErroExtrato("Valor inválido no extrato.")
        inteiro, fracao = _milhar_valido(numero, milhar), ""
    else:
        partes = numero.split(decimal)
        fracao = partes[1] if len(partes) == 2 else ""
        if len(partes) > 2 or (len(partes) == 2 and not (fracao.isdigit() and len(fracao) <= 2)):
            raise ErroExtrato("Valor inválido no extrato.")
        milhar = "." if decimal == "," else ","
        inteiro = _milhar_valido(partes[0], milhar)

    valor = int(inteiro) * 100 + int(fracao.ljust(2, "0") or "0")
    return -valor if negativo else valor


def _montar(ano: str, mes: int | str, dia: str) -> date:
    try:
        return date(int(ano), int(mes), int(dia))
    except ValueError as erro:
        raise ErroExtrato("Data inválida no extrato.") from erro


def data_texto(texto: str, formato: str | None = None) -> date:
    """Datas dos extratos: 05/09/2026, 05-09-2026, 2026-09-05, 20260905…, 5 de setembro de 2026."""
    limpo = texto.strip()
    if formato is not None:
        achado = FORMATOS_DATA[formato].fullmatch(limpo)
        if not achado:
            raise ErroExtrato("Data inválida no extrato.")
        return _montar(achado["a"], achado["m"], achado["d"])

    for nome in _AUTOMATICOS:
        if achado := FORMATOS_DATA[nome].fullmatch(limpo):
            return _montar(achado["a"], achado["m"], achado["d"])
    if achado := _COMPACTA.fullmatch(limpo):
        return _montar(achado["a"], achado["m"], achado["d"])
    if achado := _EXTENSO.fullmatch(_sem_acentos(limpo).lower()):
        nome_mes = achado["mes"]
        mes = _MESES.get(nome_mes) or (_MESES_ABREV.get(nome_mes) if len(nome_mes) == 3 else None)
        if mes is None:
            raise ErroExtrato("Data inválida no extrato.")
        return _montar(achado["a"], mes, achado["d"])
    raise ErroExtrato("Data inválida no extrato.")


def decodificar(conteudo: bytes) -> str:
    """UTF-8 (com ou sem BOM); se não for, latin-1, comum em extratos antigos."""
    try:
        texto = conteudo.decode("utf-8")
    except UnicodeDecodeError:
        texto = conteudo.decode("latin-1")
    return texto.removeprefix("﻿")


def normalizar_texto(texto: str) -> str:
    """Minúsculas, sem acentos e com espaços simples."""
    return " ".join(_sem_acentos(texto).lower().split())
