from datetime import date

import pytest

from app.domain.servico import MAX_DESCRICAO_LANCAMENTO, descricao_do_lancamento, situacao

HOJE = date(2026, 10, 15)


class TestSituacao:
    @pytest.mark.parametrize("data_prevista", [date(2026, 10, 14), HOJE, date(2026, 12, 1)])
    def test_realizado_e_recebido_em_qualquer_data(self, data_prevista: date) -> None:
        assert situacao("realizado", data_prevista, HOJE) == "recebido"

    def test_previsto_para_ontem_esta_atrasado(self) -> None:
        assert situacao("previsto", date(2026, 10, 14), HOJE) == "atrasado"

    @pytest.mark.parametrize("data_prevista", [HOJE, date(2026, 10, 16)])
    def test_previsto_para_hoje_ou_depois_esta_a_receber(self, data_prevista: date) -> None:
        assert situacao("previsto", data_prevista, HOJE) == "a_receber"

    def test_virada_de_ano(self) -> None:
        assert situacao("previsto", date(2026, 12, 31), date(2027, 1, 1)) == "atrasado"


class TestDescricaoDoLancamento:
    def test_so_o_cliente(self) -> None:
        assert descricao_do_lancamento("Loja da Maria", None) == "Loja da Maria"

    def test_cliente_e_descricao(self) -> None:
        assert descricao_do_lancamento("Loja da Maria", "Site") == "Loja da Maria — Site"

    def test_corta_no_limite_do_lancamento(self) -> None:
        texto = descricao_do_lancamento("C" * 120, "D" * 200)
        assert len(texto) == MAX_DESCRICAO_LANCAMENTO == 200
        assert texto.startswith("C" * 120 + " — ")
