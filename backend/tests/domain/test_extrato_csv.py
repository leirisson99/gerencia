from datetime import date
from pathlib import Path

import pytest

from app.domain.extrato import ErroExtrato, LinhaExtrato
from app.domain.extrato.csv import MapeamentoCsv, ler_csv_generico, ler_csv_inter, ler_csv_nubank
from app.domain.extrato.valores import decodificar

FIXTURES = Path(__file__).parent / "fixtures" / "extratos"


def _texto(nome: str) -> str:
    return decodificar((FIXTURES / nome).read_bytes())


def test_csv_nubank() -> None:
    assert ler_csv_nubank(_texto("nubank.csv")) == [
        LinhaExtrato(
            date(2026, 9, 2),
            30_000,
            "Transferência recebida pelo Pix - FULANO DE TAL",
            "1a2b3c4d-0000-4000-8000-000000000001",
        ),
        LinhaExtrato(
            date(2026, 9, 3),
            -800,
            "Compra no débito - Café, Açaí",
            "1a2b3c4d-0000-4000-8000-000000000002",
        ),
        LinhaExtrato(
            date(2026, 9, 3),
            -123_456,
            "Pagamento de boleto",
            "1a2b3c4d-0000-4000-8000-000000000003",
        ),
    ]


def test_csv_nubank_com_outro_cabecalho_e_recusado() -> None:
    with pytest.raises(ErroExtrato):
        ler_csv_nubank(_texto("inter.csv"))


def test_csv_inter_pula_preambulo_e_junta_historico_e_descricao() -> None:
    assert ler_csv_inter(_texto("inter.csv")) == [
        LinhaExtrato(date(2026, 9, 5), 500_000, "Pix recebido: Cp :00000000-Empresa Exemplo Ltda"),
        LinhaExtrato(date(2026, 9, 6), -4_590, "Pix enviado: Cp :00000000-Padaria Central"),
        LinhaExtrato(date(2026, 9, 6), -123_456, "Pagamento efetuado: Aluguel"),
    ]


def test_csv_inter_sem_cabecalho_e_recusado() -> None:
    with pytest.raises(ErroExtrato):
        ler_csv_inter(_texto("nubank.csv"))


def _mapa(**campos: object) -> MapeamentoCsv:
    padrao: dict[str, object] = {
        "separador": ";",
        "pular_linhas": 0,
        "tem_cabecalho": True,
        "coluna_data": 0,
        "formato_data": "dd/mm/aaaa",
        "coluna_descricao": 1,
        "coluna_valor": None,
        "coluna_credito": 2,
        "coluna_debito": 3,
        "separador_decimal": ",",
    }
    padrao.update(campos)
    return MapeamentoCsv(**padrao)  # type: ignore[arg-type]


def test_csv_generico_credito_e_debito_em_latin1() -> None:
    assert ler_csv_generico(_texto("generico_latin1.csv"), _mapa()) == [
        LinhaExtrato(date(2026, 10, 1), 500_000, "Salário"),
        LinhaExtrato(date(2026, 10, 2), -12_345, "Mercado"),
    ]


def test_csv_generico_coluna_de_valor_unica() -> None:
    texto = "2026-10-01,Loja,-10.50\n2026-10-02,Reembolso,20\n"
    mapa = _mapa(
        separador=",",
        tem_cabecalho=False,
        formato_data="aaaa-mm-dd",
        coluna_valor=2,
        coluna_credito=None,
        coluna_debito=None,
        separador_decimal=".",
    )
    assert ler_csv_generico(texto, mapa) == [
        LinhaExtrato(date(2026, 10, 1), -1_050, "Loja"),
        LinhaExtrato(date(2026, 10, 2), 2_000, "Reembolso"),
    ]


def test_csv_generico_pula_linhas_iniciais_e_usa_tab() -> None:
    texto = "Banco X\nConta 1\ndata\tdesc\tvalor\n09/05/2026\tCafé\t-8,00\n"
    mapa = _mapa(
        separador="\t",
        pular_linhas=2,
        formato_data="mm/dd/aaaa",
        coluna_valor=2,
        coluna_credito=None,
        coluna_debito=None,
    )
    assert ler_csv_generico(texto, mapa) == [LinhaExtrato(date(2026, 9, 5), -800, "Café")]


def test_csv_generico_debito_negativo_continua_saida() -> None:
    texto = "data;desc;cred;deb\n01/10/2026;Mercado;;-123,45\n"
    assert ler_csv_generico(texto, _mapa())[0].valor == -12_345


def test_csv_generico_coluna_inexistente_informa_a_linha() -> None:
    with pytest.raises(ErroExtrato, match="Linha 2"):
        ler_csv_generico("data;desc\n01/10/2026;Café\n", _mapa(coluna_valor=5))


def test_csv_generico_data_fora_do_formato() -> None:
    with pytest.raises(ErroExtrato, match="Linha 2"):
        ler_csv_generico("data;desc;cred;deb\n2026-10-01;Café;;8,00\n", _mapa())


def test_csv_generico_linha_sem_credito_nem_debito() -> None:
    with pytest.raises(ErroExtrato, match="Linha 2"):
        ler_csv_generico("data;desc;cred;deb\n01/10/2026;Café;;\n", _mapa())
