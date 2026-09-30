"""Leitores de extrato em PDF, um por banco, sobre as linhas já extraídas do arquivo.

Cada leitor exige a marca do seu layout (cabeçalho da tabela ou do dia). Sem ela, o PDF é
recusado em vez de gerar linhas erradas: layout de PDF muda e OFX/CSV são mais confiáveis.
"""

import re
from collections.abc import Callable, Iterable
from datetime import date

from app.domain.extrato import ErroExtrato, LinhaExtrato, LinhaPdf
from app.domain.extrato.valores import centavos, data_texto, normalizar_texto

_VALOR = r"[\d.]+,\d{2}"


def _nao_reconhecido(banco: str) -> ErroExtrato:
    return ErroExtrato(
        f"Layout de PDF não reconhecido para o {banco}. Envie o extrato em OFX ou CSV, "
        "se o banco oferecer, ou confira se escolheu o banco certo."
    )


def _exigir_marca(linhas: Iterable[LinhaPdf], banco: str, marca: Callable[[str], bool]) -> None:
    if not any(marca(linha.texto) for linha in linhas):
        raise _nao_reconhecido(banco)


def _juntar(*partes: str) -> str:
    return " ".join(" ".join(partes).split())


# Itaú: "02/07/2026 FATURA PAGA ITAU GOLD -850,40"; "SALDO DO DIA" e "SALDO ANTERIOR" não são
# movimentações.
_ITAU = re.compile(rf"(\d{{2}}/\d{{2}}/\d{{4}}) (.+?) (-?{_VALOR})")


def ler_pdf_itau(linhas: list[LinhaPdf]) -> list[LinhaExtrato]:
    _exigir_marca(
        linhas, "Itaú", lambda t: normalizar_texto(t).startswith("data lancamentos valor")
    )
    resultado = []
    for linha in linhas:
        achado = _ITAU.fullmatch(linha.texto.strip())
        if achado is None or achado[2].upper().startswith("SALDO"):
            continue
        resultado.append(
            LinhaExtrato(data_texto(achado[1]), centavos(achado[3]), _juntar(achado[2]))
        )
    return resultado


# Mercado Pago: a linha da data traz o ID da operação, o valor e o saldo; a descrição fica
# quebrada em linhas acima e abaixo, na coluna de descrição.
_MP = re.compile(rf"(\d{{2}}-\d{{2}}-\d{{4}}) ?(.*?) ?(\d{{8,}}) R\$ (-?{_VALOR}) R\$ -?{_VALOR}")
_MP_COLUNA_DESCRICAO = (70.0, 140.0)


def ler_pdf_mercado_pago(linhas: list[LinhaPdf]) -> list[LinhaExtrato]:
    _exigir_marca(linhas, "Mercado Pago", lambda t: "id da operacao" in normalizar_texto(t))
    ancoras = [(linha, _MP.fullmatch(linha.texto.strip())) for linha in linhas]
    ancoras_validas = [(linha, achado) for linha, achado in ancoras if achado]
    pedacos: dict[int, list[tuple[float, str]]] = {
        id(linha): [(linha.topo, achado[2])] for linha, achado in ancoras_validas
    }
    minimo, maximo = _MP_COLUNA_DESCRICAO
    for linha, achado in ancoras:
        if achado or not minimo <= linha.esquerda <= maximo:
            continue
        mesma_pagina = [a for a, _ in ancoras_validas if a.pagina == linha.pagina]
        if not mesma_pagina:
            continue
        mais_proxima = min(mesma_pagina, key=lambda a: abs(a.topo - linha.topo))
        pedacos[id(mais_proxima)].append((linha.topo, linha.texto))

    return [
        LinhaExtrato(
            data_texto(achado[1]),
            centavos(achado[4]),
            _juntar(*(texto for _, texto in sorted(pedacos[id(linha)]))),
            achado[3],
        )
        for linha, achado in ancoras_validas
    ]


# Neon: "Pagamento Fatura 06/09/2026 18?42 ?R$ 380,10 R$ 69,90 -". O PDF troca ":" e o sinal de
# menos por um caractere nulo.
_NEON = re.compile(
    rf"(.+?) (\d{{2}}/\d{{2}}/\d{{4}}) \d{{2}}\W?\d{{2}} ([\x00\-−]?)R\$ ({_VALOR}) "
    rf"[\x00\-−]?R\$ {_VALOR}(?: .*)?"
)


def ler_pdf_neon(linhas: list[LinhaPdf]) -> list[LinhaExtrato]:
    _exigir_marca(
        linhas, "Neon", lambda t: "descricao data hora valor saldo" in normalizar_texto(t)
    )
    resultado = []
    for linha in linhas:
        achado = _NEON.fullmatch(linha.texto.strip())
        if achado is None:
            continue
        valor = centavos(achado[4])
        resultado.append(
            LinhaExtrato(data_texto(achado[2]), -valor if achado[3] else valor, _juntar(achado[1]))
        )
    return resultado


# Nubank: dias ("02 SET 2026 Total de entradas + 300,00") com blocos de entradas e de saídas; cada
# movimentação na coluna da esquerda termina no valor (sem sinal) e continua em linhas abaixo.
_NU_DIA = re.compile(r"(\d{2} [A-Z]{3} \d{4}) Total de (entradas|saídas).*")
_NU_BLOCO = re.compile(r"Total de (entradas|saídas)\b.*")
_NU_MOVIMENTO = re.compile(rf"(.+?) ({_VALOR})")
_NU_RODAPE = re.compile(r"Extrato gerado dia .*")
_NU_COLUNA_MOVIMENTO = (100.0, 200.0)
_NU_COLUNA_DETALHE = 250.0


def ler_pdf_nubank(linhas: list[LinhaPdf]) -> list[LinhaExtrato]:
    _exigir_marca(linhas, "Nubank", lambda t: _NU_DIA.fullmatch(t.strip()) is not None)
    resultado: list[LinhaExtrato] = []
    dia: date | None = None
    sinal = 1
    pagina_atual: int | None = None
    # Movimentação em andamento: data, valor e as partes da descrição.
    atual: tuple[date, int, list[str]] | None = None

    def fechar() -> None:
        nonlocal atual
        if atual is not None:
            data, valor, partes = atual
            resultado.append(LinhaExtrato(data, valor, _juntar(*partes)))
        atual = None

    minimo, maximo = _NU_COLUNA_MOVIMENTO
    for linha in linhas:
        texto = linha.texto.strip()
        if linha.pagina != pagina_atual:
            fechar()
            pagina_atual = linha.pagina
        if achado := _NU_DIA.fullmatch(texto):
            fechar()
            dia, sinal = data_texto(achado[1]), 1 if achado[2] == "entradas" else -1
            continue
        if dia is None or _NU_RODAPE.fullmatch(texto):
            continue
        if minimo <= linha.esquerda <= maximo:
            if achado := _NU_BLOCO.fullmatch(texto):
                fechar()
                sinal = 1 if achado[1] == "entradas" else -1
            elif achado := _NU_MOVIMENTO.fullmatch(texto):
                fechar()
                atual = (dia, sinal * centavos(achado[2]), [achado[1].rstrip(" -")])
            elif atual is not None:
                atual[2].append(texto)
        elif linha.esquerda >= _NU_COLUNA_DETALHE and atual is not None:
            atual[2].append(texto)
    fechar()
    return resultado


# Inter: cabeçalho do dia ("5 de Setembro de 2026 Saldo do dia: …") e as movimentações abaixo,
# com valor e saldo: 'Pix enviado: "Cp :…" -R$ 45,90 R$ 4.954,10'.
_INTER_DIA = re.compile(r"(\d{1,2} de \w+ de \d{4}) Saldo do dia:.*")
_INTER_MOVIMENTO = re.compile(rf"(.+?) (-?R\$ {_VALOR}) -?R\$ {_VALOR}")


def ler_pdf_inter(linhas: list[LinhaPdf]) -> list[LinhaExtrato]:
    _exigir_marca(linhas, "Inter", lambda t: _INTER_DIA.fullmatch(t.strip()) is not None)
    resultado = []
    dia = None
    for linha in linhas:
        texto = linha.texto.strip()
        if achado := _INTER_DIA.fullmatch(texto):
            dia = data_texto(achado[1])
            continue
        if dia is None or (achado := _INTER_MOVIMENTO.fullmatch(texto)) is None:
            continue
        resultado.append(
            LinhaExtrato(dia, centavos(achado[2]), _juntar(achado[1].replace('"', "")))
        )
    return resultado
