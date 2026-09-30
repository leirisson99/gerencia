from datetime import date

import pytest

from app.domain.extrato import ErroExtrato
from app.domain.extrato.valores import centavos, data_texto, decodificar


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("1.234,56", 123_456),
        ("1234,56", 123_456),
        ("1234.56", 123_456),
        ("12.34", 1_234),
        ("-12.34", -1_234),
        ("-R$ 1.234,56", -123_456),
        ("R$ -1.234,56", -123_456),
        ("R$ 999,99", 99_999),
        ("+ 999,99", 99_999),
        ("- 999,99", -99_999),
        ("0,00", 0),
        ("1.234.567,89", 123_456_789),
        ("1,234,567.89", 123_456_789),
        ("1.234", 123_400),  # milhar sem centavos
        ("15", 1_500),
        (" 7,05 ", 705),
        ("−3,10", -310),  # sinal de menos tipográfico
    ],
)
def test_centavos(texto: str, esperado: int) -> None:
    assert centavos(texto) == esperado


@pytest.mark.parametrize("texto", ["", "abc", "1,2", "1,234,5", "R$", "12.345.6", "1..2"])
def test_centavos_invalido(texto: str) -> None:
    with pytest.raises(ErroExtrato):
        centavos(texto)


def test_centavos_com_separador_decimal_explicito() -> None:
    assert centavos("1.234", decimal=",") == 123_400
    assert centavos("1,5", decimal=",") == 150
    assert centavos("1.5", decimal=".") == 150
    assert centavos("1,234.56", decimal=".") == 123_456
    with pytest.raises(ErroExtrato):
        centavos("1.234", decimal=".")  # três casas decimais: nunca arredonda


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("05/09/2026", date(2026, 9, 5)),
        ("05-09-2026", date(2026, 9, 5)),
        ("2026-09-05", date(2026, 9, 5)),
        ("20260905", date(2026, 9, 5)),
        ("20260905120000[-3:BRT]", date(2026, 9, 5)),
        ("20260905000000.000", date(2026, 9, 5)),
        ("5 de setembro de 2026", date(2026, 9, 5)),
        ("05 de Março de 2026", date(2026, 3, 5)),
        ("05 SET 2026", date(2026, 9, 5)),
        ("31 DEZ 2026", date(2026, 12, 31)),
    ],
)
def test_data_texto(texto: str, esperado: date) -> None:
    assert data_texto(texto) == esperado


def test_data_texto_com_formato_explicito() -> None:
    assert data_texto("09/05/2026", formato="mm/dd/aaaa") == date(2026, 9, 5)
    assert data_texto("05/09/2026", formato="dd/mm/aaaa") == date(2026, 9, 5)


@pytest.mark.parametrize("texto", ["", "32/01/2026", "2026", "5 de brumário de 2026", "ontem"])
def test_data_texto_invalida(texto: str) -> None:
    with pytest.raises(ErroExtrato):
        data_texto(texto)


def test_decodificar_utf8_latin1_e_bom() -> None:
    assert decodificar("Descrição".encode()) == "Descrição"
    assert decodificar("Descrição".encode("latin-1")) == "Descrição"
    assert decodificar(b"\xef\xbb\xbfData") == "Data"
