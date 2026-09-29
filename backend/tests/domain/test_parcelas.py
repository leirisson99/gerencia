from datetime import date

import pytest

from app.domain.parcelas import Situacao, datas_das_parcelas, dividir, situacao


class TestDividir:
    def test_resto_vai_para_a_ultima(self) -> None:
        assert dividir(100_000, 3) == [33_333, 33_333, 33_334]

    def test_divisao_exata(self) -> None:
        assert dividir(90_000, 3) == [30_000, 30_000, 30_000]

    def test_uma_parcela(self) -> None:
        assert dividir(12_345, 1) == [12_345]

    def test_total_igual_ao_numero_de_parcelas(self) -> None:
        assert dividir(5, 5) == [1, 1, 1, 1, 1]

    @pytest.mark.parametrize(("total", "n"), [(1, 1), (7, 3), (100_001, 12), (99_999_999_999, 120)])
    def test_soma_e_sempre_o_total(self, total: int, n: int) -> None:
        parcelas = dividir(total, n)
        assert len(parcelas) == n
        assert sum(parcelas) == total
        assert all(p == total // n for p in parcelas[:-1])

    @pytest.mark.parametrize(("total", "n"), [(0, 1), (10, 0), (3, 5)])
    def test_entradas_invalidas(self, total: int, n: int) -> None:
        with pytest.raises(ValueError):
            dividir(total, n)


class TestDatasDasParcelas:
    def test_meses_seguidos_no_dia_do_vencimento(self) -> None:
        assert datas_das_parcelas(15, date(2026, 10, 5), 3) == [
            date(2026, 10, 15),
            date(2026, 11, 15),
            date(2026, 12, 15),
        ]

    def test_primeira_no_mes_seguinte_se_o_dia_ja_passou(self) -> None:
        assert datas_das_parcelas(1, date(2026, 10, 5), 2) == [date(2026, 11, 1), date(2026, 12, 1)]

    def test_fim_de_mes_limitado_sem_perder_o_dia(self) -> None:
        assert datas_das_parcelas(31, date(2026, 1, 10), 4) == [
            date(2026, 1, 31),
            date(2026, 2, 28),
            date(2026, 3, 31),
            date(2026, 4, 30),
        ]

    def test_virada_de_ano(self) -> None:
        assert datas_das_parcelas(10, date(2026, 11, 20), 3) == [
            date(2026, 12, 10),
            date(2027, 1, 10),
            date(2027, 2, 10),
        ]

    def test_primeira_no_proprio_inicio(self) -> None:
        assert datas_das_parcelas(5, date(2026, 10, 5), 1) == [date(2026, 10, 5)]


class TestSituacao:
    def test_nada_pago(self) -> None:
        assert situacao([(33_333, False), (33_333, False), (33_334, False)]) == Situacao(
            pagas=0, total=3, valor_pago=0, valor_restante=100_000, quitada=False
        )

    def test_parte_paga(self) -> None:
        assert situacao([(33_333, True), (33_333, False), (33_334, False)]) == Situacao(
            pagas=1, total=3, valor_pago=33_333, valor_restante=66_667, quitada=False
        )

    def test_quitada(self) -> None:
        resultado = situacao([(50_000, True), (50_000, True)])
        assert (resultado.quitada, resultado.valor_restante) == (True, 0)
