"""CSV de extrato: layouts do Nubank e do Inter, e o genérico com colunas do usuário."""

import csv
import io
from dataclasses import dataclass

from app.domain.extrato import ErroExtrato, LinhaExtrato
from app.domain.extrato.valores import centavos, data_texto, normalizar_texto


@dataclass(frozen=True)
class MapeamentoCsv:
    """Colunas contadas a partir de 0. Use `coluna_valor` ou o par crédito/débito."""

    separador: str
    pular_linhas: int
    tem_cabecalho: bool
    coluna_data: int
    formato_data: str
    coluna_descricao: int
    coluna_valor: int | None
    coluna_credito: int | None
    coluna_debito: int | None
    separador_decimal: str


def _registros(texto: str, separador: str) -> list[list[str]]:
    return [
        [campo.strip() for campo in registro]
        for registro in csv.reader(io.StringIO(texto), delimiter=separador)
    ]


def _cabecalho(registro: list[str]) -> list[str]:
    return [normalizar_texto(campo) for campo in registro]


def _na_linha(numero: int, erro: ErroExtrato) -> ErroExtrato:
    return ErroExtrato(f"Linha {numero}: {erro}")


def ler_csv_nubank(texto: str) -> list[LinhaExtrato]:
    registros = _registros(texto, ",")
    if not registros or _cabecalho(registros[0])[:3] != ["data", "valor", "identificador"]:
        raise ErroExtrato("O arquivo não é um CSV de conta do Nubank.")
    linhas = []
    for numero, registro in enumerate(registros[1:], start=2):
        if not any(registro):
            continue
        try:
            data, valor, identificador, *descricao = registro
            linhas.append(
                LinhaExtrato(
                    data=data_texto(data, "dd/mm/aaaa"),
                    valor=centavos(valor, decimal="."),
                    descricao=",".join(descricao).strip(),
                    id_origem=identificador or None,
                )
            )
        except ErroExtrato as erro:
            raise _na_linha(numero, erro) from erro
        except ValueError as erro:
            raise _na_linha(numero, ErroExtrato("colunas faltando.")) from erro
    return linhas


def ler_csv_inter(texto: str) -> list[LinhaExtrato]:
    """Preâmbulo (conta, período, saldo) e a tabela `Data Lançamento;Histórico;…;Valor;Saldo`."""
    registros = _registros(texto, ";")
    inicio = next(
        (i for i, r in enumerate(registros) if r and _cabecalho(r)[0] == "data lancamento"), None
    )
    if inicio is None:
        raise ErroExtrato("O arquivo não é um CSV de conta do Inter.")
    linhas = []
    for numero, registro in enumerate(registros[inicio + 1 :], start=inicio + 2):
        if not any(registro):
            continue
        try:
            data, historico, descricao, valor, *_ = registro
            linhas.append(
                LinhaExtrato(
                    data=data_texto(data, "dd/mm/aaaa"),
                    valor=centavos(valor, decimal=","),
                    descricao=": ".join(parte for parte in (historico, descricao) if parte),
                )
            )
        except ErroExtrato as erro:
            raise _na_linha(numero, erro) from erro
        except ValueError as erro:
            raise _na_linha(numero, ErroExtrato("colunas faltando.")) from erro
    return linhas


def _campo(registro: list[str], coluna: int) -> str:
    if coluna >= len(registro):
        raise ErroExtrato(f"a coluna {coluna} não existe.")
    return registro[coluna]


def _valor_generico(registro: list[str], mapa: MapeamentoCsv) -> int:
    if mapa.coluna_valor is not None:
        return centavos(_campo(registro, mapa.coluna_valor), decimal=mapa.separador_decimal)
    assert mapa.coluna_credito is not None and mapa.coluna_debito is not None
    credito = _campo(registro, mapa.coluna_credito)
    debito = _campo(registro, mapa.coluna_debito)
    if credito and debito:
        raise ErroExtrato("crédito e débito preenchidos na mesma linha.")
    if credito:
        return abs(centavos(credito, decimal=mapa.separador_decimal))
    if debito:
        return -abs(centavos(debito, decimal=mapa.separador_decimal))
    raise ErroExtrato("sem valor de crédito nem de débito.")


def ler_csv_generico(texto: str, mapa: MapeamentoCsv) -> list[LinhaExtrato]:
    registros = _registros(texto, mapa.separador)
    primeira = mapa.pular_linhas + (1 if mapa.tem_cabecalho else 0)
    linhas = []
    for numero, registro in enumerate(registros[primeira:], start=primeira + 1):
        if not any(registro):
            continue
        try:
            linhas.append(
                LinhaExtrato(
                    data=data_texto(_campo(registro, mapa.coluna_data), mapa.formato_data),
                    valor=_valor_generico(registro, mapa),
                    descricao=_campo(registro, mapa.coluna_descricao),
                )
            )
        except ErroExtrato as erro:
            raise _na_linha(numero, erro) from erro
    return linhas
