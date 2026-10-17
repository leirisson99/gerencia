from datetime import UTC, date, datetime, timedelta

import pytest

from app.domain.conta_compartilhada import (
    MAX_PARTICIPANTES,
    DivisaoInvalida,
    convite_expirado,
    data_da_cota,
    ratear,
    status_da_cota,
)


class TestRatearIgual:
    @pytest.mark.parametrize(
        ("total", "n"), [(60_000, 6), (10_000, 3), (200_000, 4), (1, 1), (2, 2), (10_000, 1)]
    )
    def test_soma_e_sempre_o_total(self, total: int, n: int) -> None:
        cotas = ratear(total, "igual", [None] * n)
        assert len(cotas) == n
        assert sum(cotas) == total

    def test_resto_vai_para_a_ultima(self) -> None:
        assert ratear(10_000, "igual", [None, None, None]) == [3_333, 3_333, 3_334]

    def test_divisao_exata(self) -> None:
        assert ratear(60_000, "igual", [None] * 6) == [10_000] * 6

    def test_total_menor_que_o_numero_de_pessoas(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(1, "igual", [None, None])


class TestRatearPercentual:
    def test_soma_e_o_total_e_resto_na_ultima(self) -> None:
        # 33,33% / 33,33% / 33,34% de R$ 100,01
        cotas = ratear(10_001, "percentual", [3_333, 3_333, 3_334])
        assert sum(cotas) == 10_001
        assert cotas[:2] == [10_001 * 3_333 // 10_000] * 2

    def test_cinquenta_cinquenta(self) -> None:
        assert ratear(200_000, "percentual", [5_000, 5_000]) == [100_000, 100_000]

    @pytest.mark.parametrize("bps", [[5_000, 4_000], [6_000, 6_000], [10_001]])
    def test_percentual_que_nao_fecha_100(self, bps: list[int]) -> None:
        with pytest.raises(DivisaoInvalida) as erro:
            ratear(100_000, "percentual", bps)
        assert erro.value.diferenca == 10_000 - sum(bps)

    def test_percentual_sem_valor(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(100_000, "percentual", [5_000, None])


class TestRatearFixo:
    def test_valores_somando_o_total(self) -> None:
        assert ratear(200_000, "fixo", [120_000, 50_000, 30_000]) == [120_000, 50_000, 30_000]

    def test_falta_dinheiro(self) -> None:
        with pytest.raises(DivisaoInvalida) as erro:
            ratear(200_000, "fixo", [100_000, 50_000])
        assert erro.value.diferenca == 50_000

    def test_passa_do_total(self) -> None:
        with pytest.raises(DivisaoInvalida) as erro:
            ratear(200_000, "fixo", [150_000, 100_000])
        assert erro.value.diferenca == -50_000

    def test_fixo_sem_valor(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(200_000, "fixo", [200_000, None])


class TestCotaZerada:
    def test_percentual_que_arredonda_para_zero(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(10, "percentual", [1, 9_999])

    def test_fixo_com_participante_zerado(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(10_000, "fixo", [10_000, 0])


class TestRatearLimites:
    def test_sem_participantes(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(10_000, "igual", [])

    def test_acima_do_maximo(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(1_000_000, "igual", [None] * (MAX_PARTICIPANTES + 1))

    def test_no_maximo(self) -> None:
        assert sum(ratear(1_000_000, "igual", [None] * MAX_PARTICIPANTES)) == 1_000_000

    def test_total_zero_ou_negativo(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(0, "igual", [None, None])

    def test_modo_desconhecido(self) -> None:
        with pytest.raises(DivisaoInvalida):
            ratear(10_000, "outro", [None])


class TestStatusDaCota:
    AGORA = datetime(2026, 10, 16, 12, tzinfo=UTC)

    def test_sem_lancamento_e_pendente(self) -> None:
        assert status_da_cota(None, None) == "pendente"

    def test_previsto_e_pendente(self) -> None:
        assert status_da_cota("previsto", None) == "pendente"

    def test_realizado_e_informado(self) -> None:
        assert status_da_cota("realizado", None) == "informado"

    def test_realizado_e_confirmado(self) -> None:
        assert status_da_cota("realizado", self.AGORA) == "confirmado"

    def test_confirmacao_nao_vale_com_lancamento_previsto(self) -> None:
        assert status_da_cota("previsto", self.AGORA) == "pendente"

    def test_confirmacao_nao_vale_sem_lancamento(self) -> None:
        assert status_da_cota(None, self.AGORA) == "pendente"


class TestConviteExpirado:
    CONVITE = datetime(2026, 10, 1, 12, tzinfo=UTC)

    def test_no_trigesimo_dia_ainda_vale(self) -> None:
        assert not convite_expirado(self.CONVITE, self.CONVITE + timedelta(days=30))

    def test_depois_de_30_dias_expira(self) -> None:
        assert convite_expirado(self.CONVITE, self.CONVITE + timedelta(days=30, seconds=1))

    def test_recem_convidado(self) -> None:
        assert not convite_expirado(self.CONVITE, self.CONVITE)


class TestDataDaCota:
    def test_dia_comum(self) -> None:
        assert data_da_cota(date(2026, 10, 1), 10) == date(2026, 10, 10)

    def test_dia_31_em_mes_de_30(self) -> None:
        assert data_da_cota(date(2026, 11, 1), 31) == date(2026, 11, 30)

    def test_dia_30_em_fevereiro_bissexto(self) -> None:
        assert data_da_cota(date(2028, 2, 1), 30) == date(2028, 2, 29)
