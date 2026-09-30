"""Leitores de PDF por banco, sobre linhas sintéticas no mesmo layout dos extratos reais."""

from collections.abc import Callable
from datetime import date
from pathlib import Path

import pytest

from app.domain.extrato import ErroExtrato, LinhaExtrato, LinhaPdf
from app.domain.extrato.pdf import (
    ler_pdf_inter,
    ler_pdf_itau,
    ler_pdf_mercado_pago,
    ler_pdf_neon,
    ler_pdf_nubank,
)

FIXTURES = Path(__file__).parent / "fixtures" / "extratos"
Leitor = Callable[[list[LinhaPdf]], list[LinhaExtrato]]


def _linhas(nome: str) -> list[LinhaPdf]:
    """Cada linha da fixture: `pagina|topo|esquerda|texto`."""
    linhas = []
    for registro in (FIXTURES / nome).read_text(encoding="utf-8").splitlines():
        pagina, topo, esquerda, texto = registro.split("|", 3)
        linhas.append(LinhaPdf(int(pagina), float(topo), float(esquerda), texto))
    return linhas


def test_pdf_itau_ignora_saldos_e_junta_paginas() -> None:
    assert ler_pdf_itau(_linhas("itau_pdf.txt")) == [
        LinhaExtrato(date(2026, 7, 2), -85_040, "FATURA PAGA ITAU GOLD"),
        LinhaExtrato(date(2026, 7, 2), 150_000, "PIX TRANSF FULANO02/07"),
        LinhaExtrato(date(2026, 7, 2), -321, "JUROS LIMITE DA CONTA"),
        LinhaExtrato(date(2026, 7, 3), -1_250, "PIX QRS PADARIA CE03/07"),
        LinhaExtrato(date(2026, 7, 3), 7, "REND PAGO APLIC AUT MAIS"),
    ]


def test_pdf_mercado_pago_junta_descricao_acima_e_abaixo_da_data() -> None:
    linhas = ler_pdf_mercado_pago(_linhas("mercado_pago_pdf.txt"))
    assert linhas == [
        LinhaExtrato(
            date(2026, 9, 1),
            -4_590,
            "Pagamento com QR Pix D DOS S COMERCIO B DE Padaria Central",
            "111111111111",
        ),
        LinhaExtrato(date(2026, 9, 2), -2_000, "Pix enviado Fulano de Tal", "222222222222"),
        LinhaExtrato(date(2026, 9, 2), 5, "Rendimentos", "3333333333333"),
        LinhaExtrato(date(2026, 9, 3), 100_000, "Dinheiro recebido de Empresa", "444444444444"),
        LinhaExtrato(date(2026, 9, 4), -305, "Pagamento Mp*Loja", "555555555555"),
        LinhaExtrato(date(2026, 9, 5), 1_995, "Pix recebido Beltrano", "666666666666"),
    ]
    # Bate com os totais impressos no extrato (Entradas R$ 1.020,00; Saídas R$ -68,95).
    assert sum(lin.valor for lin in linhas if lin.valor > 0) == 102_000
    assert sum(lin.valor for lin in linhas if lin.valor < 0) == -6_895


def test_pdf_neon_sinal_trocado_por_caractere_nulo_e_hora_ignorada() -> None:
    assert ler_pdf_neon(_linhas("neon_pdf.txt")) == [
        LinhaExtrato(date(2026, 9, 5), 45_000, "PIX recebido de Fulano de Tal"),
        LinhaExtrato(date(2026, 9, 6), -38_010, "Pagamento Fatura"),
        LinhaExtrato(date(2026, 9, 7), -990, "Compra débito Mercado"),
    ]


def test_pdf_nubank_blocos_de_entradas_e_saidas_e_continuacoes() -> None:
    assert ler_pdf_nubank(_linhas("nubank_pdf.txt")) == [
        LinhaExtrato(
            date(2026, 9, 2),
            30_000,
            "Transferência recebida pelo Pix FULANO DE TAL - •••.000.000-•• "
            "BANCO EXEMPLO IP S.A. (0000) Agência: 1 Conta: 1234567-8",
        ),
        LinhaExtrato(date(2026, 9, 2), -42_000, "Pagamento de fatura"),
        LinhaExtrato(
            date(2026, 9, 5),
            25_100,
            "Valor adicionado na conta por Valor adicionado Pix no Crédito cartão de crédito",
        ),
        # Página 2 continua o dia 05 da página anterior, agora no bloco de saídas.
        LinhaExtrato(
            date(2026, 9, 5),
            -13_000,
            "Transferência enviada pelo Pix LOJA EXEMPLO LTDA - 00.000.000 "
            "/0001-00 - BANCO EXEMPLO IP S.A. Agência: 1 Conta: 12345-6",
        ),
    ]


def test_pdf_inter_data_do_cabecalho_do_dia_e_sem_aspas() -> None:
    assert ler_pdf_inter(_linhas("inter_pdf.txt")) == [
        LinhaExtrato(date(2026, 9, 5), 500_000, "Pix recebido: Cp :00000000-Empresa Exemplo Ltda"),
        LinhaExtrato(date(2026, 9, 5), -4_590, "Pix enviado: Cp :00000000-Padaria Central"),
        LinhaExtrato(date(2026, 9, 6), -123_456, "Pagamento efetuado: Aluguel"),
        LinhaExtrato(date(2026, 9, 7), -372_954, "Pix enviado: Cp :00000000-Loja"),
    ]


LEITORES: dict[str, Leitor] = {
    "itau": ler_pdf_itau,
    "mercado_pago": ler_pdf_mercado_pago,
    "neon": ler_pdf_neon,
    "nubank": ler_pdf_nubank,
    "inter": ler_pdf_inter,
}


@pytest.mark.parametrize("banco", LEITORES)
@pytest.mark.parametrize("outro", LEITORES)
def test_pdf_de_outro_banco_e_recusado(banco: str, outro: str) -> None:
    if banco == outro:
        return
    with pytest.raises(ErroExtrato, match="não reconhecido"):
        LEITORES[banco](_linhas(f"{outro}_pdf.txt"))


@pytest.mark.parametrize("banco", LEITORES)
def test_pdf_vazio_e_recusado(banco: str) -> None:
    with pytest.raises(ErroExtrato):
        LEITORES[banco]([])
