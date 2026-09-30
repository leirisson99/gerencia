from datetime import date
from pathlib import Path

import pytest

from app.domain.extrato import ErroExtrato, LinhaExtrato
from app.domain.extrato.ofx import ler_ofx
from app.domain.extrato.valores import decodificar

FIXTURES = Path(__file__).parent / "fixtures" / "extratos"


def _ler(nome: str) -> list[LinhaExtrato]:
    return ler_ofx(decodificar((FIXTURES / nome).read_bytes()))


def test_ofx_sgml_com_fechamento_de_tags() -> None:
    assert _ler("inter.ofx") == [
        LinhaExtrato(
            date(2026, 9, 5), 500_000, "Pix recebido: Empresa Exemplo Ltda", "202609050001"
        ),
        LinhaExtrato(date(2026, 9, 6), -4_590, "Pix enviado: Padaria Central", "202609060002"),
        LinhaExtrato(date(2026, 9, 6), -123_456, "Pagamento de boleto: Aluguel", "202609060003"),
    ]


def test_ofx_com_fuso_na_data_e_acentos() -> None:
    linhas = _ler("nubank.ofx")
    assert [(lin.data, lin.valor) for lin in linhas] == [
        (date(2026, 9, 2), 30_000),
        (date(2026, 9, 3), -800),
    ]
    assert linhas[1].descricao == "Compra no débito - Café Açaí"
    assert linhas[1].id_origem == "1a2b3c4d-0000-4000-8000-000000000002"


def test_ofx_xml_usa_name_sem_memo_e_virgula_decimal() -> None:
    assert _ler("xml2.ofx") == [LinhaExtrato(date(2026, 10, 1), -150, "Tarifa", "X1")]


def test_ofx_sgml_sem_fechamento_das_folhas() -> None:
    assert _ler("sgml_sem_fechamento.ofx") == [
        LinhaExtrato(date(2026, 10, 2), -1_990, "Assinatura streaming", "SEMFECHAR1")
    ]


def test_ofx_sem_movimentacoes() -> None:
    assert ler_ofx("OFXHEADER:100\n<OFX><BANKTRANLIST></BANKTRANLIST></OFX>") == []


def test_ofx_espacos_e_entidades_na_descricao() -> None:
    texto = (
        "<OFX><STMTTRN><DTPOSTED>20261003<TRNAMT>-5.00<FITID>A"
        "<MEMO>  Mercado &amp; Cia   Ltda  </STMTTRN></OFX>"
    )
    assert ler_ofx(texto)[0].descricao == "Mercado & Cia Ltda"


@pytest.mark.parametrize(
    "texto",
    [
        "Data,Valor\n01/01/2026,10.00\n",  # CSV, não OFX
        "<OFX><STMTTRN><DTPOSTED>20261003<FITID>A</STMTTRN></OFX>",  # sem TRNAMT
        "<OFX><STMTTRN><DTPOSTED>ontem<TRNAMT>1.00</STMTTRN></OFX>",  # data inválida
    ],
)
def test_ofx_invalido(texto: str) -> None:
    with pytest.raises(ErroExtrato):
        ler_ofx(texto)
