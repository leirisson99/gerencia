from datetime import date

from app.domain.painel import ranking_formas, serie_mensal, ultimos_meses

HOJE = date(2026, 9, 30)


class TestUltimosMeses:
    def test_doze_meses_do_mais_antigo_ao_atual(self) -> None:
        meses = ultimos_meses(HOJE, 12)

        assert len(meses) == 12
        assert meses[0] == date(2025, 10, 1)
        assert meses[-1] == date(2026, 9, 1)

    def test_atravessa_a_virada_de_ano(self) -> None:
        assert ultimos_meses(date(2027, 2, 10), 3) == [
            date(2026, 12, 1),
            date(2027, 1, 1),
            date(2027, 2, 1),
        ]

    def test_primeiro_dia_do_mes(self) -> None:
        assert ultimos_meses(date(2026, 3, 1), 1) == [date(2026, 3, 1)]


class TestSerieMensal:
    def test_preenche_meses_sem_movimento_com_zero(self) -> None:
        meses = ultimos_meses(HOJE, 3)
        contagens = {(date(2026, 7, 1), "entrada"): 2, (date(2026, 9, 1), "saida"): 5}

        assert serie_mensal(contagens, meses) == [
            (date(2026, 7, 1), 2, 0),
            (date(2026, 8, 1), 0, 0),
            (date(2026, 9, 1), 0, 5),
        ]

    def test_ignora_meses_fora_da_janela(self) -> None:
        meses = ultimos_meses(HOJE, 1)
        contagens = {(date(2026, 8, 1), "entrada"): 9, (date(2026, 9, 1), "entrada"): 1}

        assert serie_mensal(contagens, meses) == [(date(2026, 9, 1), 1, 0)]


class TestRankingFormas:
    def test_mais_usada_primeiro_e_todas_as_formas(self) -> None:
        assert ranking_formas({"cartao": 3, "pix": 7}) == [
            ("pix", 7),
            ("cartao", 3),
            ("boleto", 0),
            ("dinheiro", 0),
        ]

    def test_empate_segue_a_ordem_fixa(self) -> None:
        assert ranking_formas({"dinheiro": 1, "boleto": 1}) == [
            ("boleto", 1),
            ("dinheiro", 1),
            ("pix", 0),
            ("cartao", 0),
        ]

    def test_sem_dividas(self) -> None:
        assert ranking_formas({}) == [("pix", 0), ("boleto", 0), ("cartao", 0), ("dinheiro", 0)]
