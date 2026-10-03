from datetime import date

from app.domain.retirada import Lado, lados_da_retirada, validar_retirada

HOJE = date(2026, 10, 15)


class TestValidarRetirada:
    def test_valida(self) -> None:
        assert validar_retirada(500_000, HOJE, HOJE) == {}
        assert validar_retirada(1, date(2026, 1, 1), HOJE) == {}

    def test_valor_zero_ou_negativo(self) -> None:
        assert set(validar_retirada(0, HOJE, HOJE)) == {"valor"}
        assert set(validar_retirada(-5, HOJE, HOJE)) == {"valor"}

    def test_data_futura(self) -> None:
        assert set(validar_retirada(100, date(2026, 10, 16), HOJE)) == {"data"}

    def test_os_dois_problemas(self) -> None:
        assert set(validar_retirada(0, date(2026, 10, 16), HOJE)) == {"valor", "data"}


def test_lados_tem_mesmo_valor_e_data() -> None:
    pj, pf = lados_da_retirada(500_000, date(2026, 10, 25))

    assert pj == Lado(carteira="pj", tipo="saida", valor=500_000, data=date(2026, 10, 25))
    assert pf == Lado(carteira="pf", tipo="entrada", valor=500_000, data=date(2026, 10, 25))
