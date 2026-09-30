"""OFX (SGML 1.x ou XML 2.x): só as 5 tags que importam, sem depender de biblioteca."""

import html
import re

from app.domain.extrato import ErroExtrato, LinhaExtrato
from app.domain.extrato.valores import centavos, data_texto

_BLOCO = re.compile(
    r"<STMTTRN>(.*?)(?=</STMTTRN>|<STMTTRN>|</BANKTRANLIST>|\Z)", re.IGNORECASE | re.DOTALL
)


def _tag(bloco: str, nome: str) -> str | None:
    """Valor de uma folha, com ou sem tag de fechamento (SGML permite omitir)."""
    achado = re.search(rf"<{nome}>([^<\r\n]*)", bloco, re.IGNORECASE)
    if achado is None:
        return None
    valor = achado.group(1).strip()
    return valor or None


def _descricao(bloco: str) -> str:
    texto = _tag(bloco, "MEMO") or _tag(bloco, "NAME") or ""
    return " ".join(html.unescape(texto).split())


def ler_ofx(texto: str) -> list[LinhaExtrato]:
    if "<OFX>" not in texto.upper():
        raise ErroExtrato("O arquivo não é um OFX.")
    linhas = []
    for bloco in _BLOCO.findall(texto):
        valor, data = _tag(bloco, "TRNAMT"), _tag(bloco, "DTPOSTED")
        if valor is None or data is None:
            raise ErroExtrato("Movimentação do OFX sem valor ou sem data.")
        linhas.append(
            LinhaExtrato(
                data=data_texto(data),
                valor=centavos(valor),
                descricao=_descricao(bloco),
                id_origem=_tag(bloco, "FITID"),
            )
        )
    return linhas
