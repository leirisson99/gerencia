"""Leitura de extratos bancários: tudo aqui é puro (recebe texto ou linhas, devolve dados)."""

from dataclasses import dataclass
from datetime import date
from typing import Literal

Formato = Literal["ofx", "csv", "pdf", "csv_generico"]


class ErroExtrato(Exception):
    """O arquivo não pôde ser lido no formato escolhido; a mensagem vai para o usuário."""


@dataclass(frozen=True)
class LinhaExtrato:
    data: date
    valor: int  # centavos com sinal: > 0 entrada, < 0 saída
    descricao: str
    id_origem: str | None = None  # identificador do banco, quando o arquivo traz um


@dataclass(frozen=True)
class LinhaPdf:
    """Uma linha visual de uma página de PDF: posição vertical (maior = mais abaixo) e início
    horizontal, que separa as colunas do layout."""

    pagina: int
    topo: float
    esquerda: float
    texto: str
