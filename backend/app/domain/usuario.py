"""Regras puras de validação e normalização dos dados de cadastro."""

import re
from datetime import date
from typing import Literal

from email_validator import EmailNotValidError, validate_email

MAX_EMAIL = 254
MAX_NOME = 120
MAX_CARGO = 80
MIN_SENHA = 8
MAX_SENHA = 128
DATA_NASCIMENTO_MINIMA = date(1900, 1, 1)

TIPO_CLT = "clt"
TIPO_PRESTADOR = "prestador"
TIPO_CLT_PRESTADOR = "clt_prestador"
TIPOS_RENDA = (TIPO_CLT, TIPO_PRESTADOR, TIPO_CLT_PRESTADOR)

Carteira = Literal["pf", "pj"]
CARTEIRA_PADRAO: Carteira = "pf"
ProblemaPj = Literal["tipo_sem_pj", "pj_com_dados"]


def ciclo_pelo_mes(tipo_renda: str, carteira: str = CARTEIRA_PADRAO) -> bool:
    """A PJ e o prestador usam o mês do calendário; a PF de quem tem salário abre pelo salário.

    Único ponto que decide a regra do ciclo (constituição 7.0.0, princípio II).
    """
    return carteira == "pj" or tipo_renda == TIPO_PRESTADOR


def pode_ter_pj(tipo_renda: str) -> bool:
    """A carteira PJ é de quem presta serviço."""
    return tipo_renda in (TIPO_PRESTADOR, TIPO_CLT_PRESTADOR)


def verificar_pj(tem_pj_novo: bool, tipo_novo: str, tem_dados_pj: bool) -> ProblemaPj | None:
    """Ligar exige quem presta serviço; desligar (ou ir para `clt`) exige a PJ vazia."""
    if tem_pj_novo:
        return None if pode_ter_pj(tipo_novo) else "tipo_sem_pj"
    return "pj_com_dados" if tem_dados_pj else None


def tem_servicos(tipo_renda: str) -> bool:
    """Serviços a receber são só para quem presta serviço."""
    return tipo_renda in (TIPO_PRESTADOR, TIPO_CLT_PRESTADOR)


def limpar_texto(valor: str, max_len: int) -> str:
    texto = valor.strip()
    if not texto:
        raise ValueError("Campo obrigatório.")
    if len(texto) > max_len:
        raise ValueError(f"Máximo de {max_len} caracteres.")
    return texto


def normalizar_email(valor: str) -> str:
    email = valor.strip().lower()
    if len(email) > MAX_EMAIL:
        raise ValueError(f"Máximo de {MAX_EMAIL} caracteres.")
    try:
        validate_email(email, check_deliverability=False)
    except EmailNotValidError:
        raise ValueError("E-mail inválido.") from None
    return email


def normalizar_telefone(valor: str) -> str:
    """Telefone brasileiro: DDD (11–99) + 8 ou 9 dígitos; com 9 dígitos começa com 9."""
    digitos = re.sub(r"\D", "", valor)
    if len(digitos) not in (10, 11):
        raise ValueError("Informe DDD e número, com 10 ou 11 dígitos.")
    if int(digitos[:2]) < 11:
        raise ValueError("DDD inválido.")
    if len(digitos) == 11 and digitos[2] != "9":
        raise ValueError("Celular com 11 dígitos deve começar com 9 depois do DDD.")
    return digitos


def validar_senha(senha: str) -> str:
    if not MIN_SENHA <= len(senha) <= MAX_SENHA:
        raise ValueError(f"A senha deve ter entre {MIN_SENHA} e {MAX_SENHA} caracteres.")
    if not any(c.isalpha() for c in senha) or not any(c.isdigit() for c in senha):
        raise ValueError("A senha deve ter pelo menos uma letra e um número.")
    return senha


def validar_data_nascimento(data: date, hoje: date) -> date:
    if not DATA_NASCIMENTO_MINIMA <= data <= hoje:
        raise ValueError("A data de nascimento deve estar entre 01/01/1900 e hoje.")
    return data
