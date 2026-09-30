"""Regras da importação de extrato: identificação, situação das linhas, sugestão e cobertura."""

import hashlib
import string
from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from datetime import date
from typing import Literal

from app.domain.ciclo import Ciclo, ProblemaCobertura, ciclo_atual, verificar_cobertura
from app.domain.extrato import LinhaExtrato
from app.domain.extrato.valores import normalizar_texto

Situacao = Literal[
    "nova", "ja_importada", "possivel_duplicada", "antes_do_primeiro_ciclo", "invalida"
]
Tipo = Literal["entrada", "saida"]

MAX_ID_EXTERNO = 120
_PONTAS = string.punctuation + " "


def normalizar_descricao(texto: str) -> str:
    """Base da sugestão: sem diferença de maiúsculas, acentos, espaços e pontuação nas pontas."""
    return normalizar_texto(texto).strip(_PONTAS)


def tipo_da_linha(valor: int) -> Tipo:
    return "entrada" if valor > 0 else "saida"


def _hash(*partes: object) -> str:
    return hashlib.sha256("|".join(map(str, partes)).encode()).hexdigest()[:40]


def ids_externos(banco: str, formato: str, linhas: Sequence[LinhaExtrato]) -> list[str]:
    """Identificação estável de cada movimentação, para não importar duas vezes.

    Com id do banco: `banco:formato:id`. Sem id: hash de data, valor, descrição e da ordem entre
    linhas idênticas do arquivo (o 1º café de R$ 8 do dia, o 2º…).
    """
    prefixo = f"{banco}:{formato}:"
    vistos: Counter[object] = Counter()
    ids = []
    for linha in linhas:
        if linha.id_origem is not None:
            chave: object = ("id", linha.id_origem)
            ordem = vistos[chave]
            vistos[chave] += 1
            id_origem = linha.id_origem if ordem == 0 else f"{linha.id_origem}#{ordem}"
            candidato = prefixo + id_origem
            if len(candidato) > MAX_ID_EXTERNO:
                candidato = f"{prefixo}h:{_hash('id', id_origem)}"
        else:
            chave = (linha.data, linha.valor, normalizar_descricao(linha.descricao))
            ordem = vistos[chave]
            vistos[chave] += 1
            candidato = f"{prefixo}h:{_hash(linha.data.isoformat(), linha.valor, chave[2], ordem)}"
        ids.append(candidato)
    return ids


def classificar(
    linhas: Sequence[LinhaExtrato],
    ids: Sequence[str],
    ja_importados: set[str],
    existentes: Counter[tuple[date, str, int]],
    primeiro_salario: date | None,
) -> list[Situacao]:
    """Situação de cada linha na prévia, nesta precedência: inválida, já importada, antes do
    primeiro ciclo, possível duplicada, nova.

    `existentes` conta os lançamentos do usuário por (data, tipo, valor), fora os importados deste
    mesmo arquivo; cada um só marca uma linha como possível duplicada.
    """
    restantes = Counter(existentes)
    situacoes: list[Situacao] = []
    for linha, id_externo in zip(linhas, ids, strict=True):
        chave = (linha.data, tipo_da_linha(linha.valor), abs(linha.valor))
        if linha.valor == 0:
            situacoes.append("invalida")
        elif id_externo in ja_importados:
            situacoes.append("ja_importada")
        elif primeiro_salario is not None and linha.data < primeiro_salario:
            situacoes.append("antes_do_primeiro_ciclo")
        elif restantes[chave] > 0:
            restantes[chave] -= 1
            situacoes.append("possivel_duplicada")
        else:
            situacoes.append("nova")
    return situacoes


def sugerir_categoria(
    descricao: str, tipo: str, historico: Mapping[str, tuple[int, str]]
) -> int | None:
    """Categoria do lançamento mais recente com a mesma descrição normalizada, se for do mesmo
    tipo. `historico` mapeia descrição normalizada → (categoria_id, tipo). Nunca IA."""
    chave = normalizar_descricao(descricao)
    if not chave or chave not in historico:
        return None
    categoria_id, tipo_categoria = historico[chave]
    return categoria_id if tipo_categoria == tipo else None


def cobertura_do_lote(
    salarios_existentes: Iterable[date],
    menor_outros_existente: date | None,
    lote: Iterable[tuple[bool, date]],
) -> ProblemaCobertura | None:
    """Nenhum lançamento fora de ciclo depois de gravar o lote. `lote` tem (é_salário, data)."""
    salarios = list(salarios_existentes)
    menor_outros = menor_outros_existente
    for e_salario, data in lote:
        if e_salario:
            salarios.append(data)
        elif menor_outros is None or data < menor_outros:
            menor_outros = data
    return verificar_cobertura(salarios, menor_outros)


def novo_ciclo_aberto(
    salarios_existentes: Sequence[date], salarios_lote: Sequence[date]
) -> Ciclo | None:
    """O ciclo aberto que o lote cria, se trouxer um salário depois de todos os existentes.

    Só ele recebe os previstos das recorrências; ciclos do passado ficam como estão.
    """
    if not salarios_lote:
        return None
    if salarios_existentes and max(salarios_lote) <= max(salarios_existentes):
        return None
    return ciclo_atual([*salarios_existentes, *salarios_lote])
