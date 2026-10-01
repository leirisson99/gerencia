from datetime import date, timedelta

import pytest

from app.domain.lembrete import (
    JANELA_DIAS,
    Contagem,
    Mensagem,
    Total,
    contar,
    limite,
    situacao,
    texto_resumo,
)

HOJE = date(2026, 10, 14)  # quarta-feira; a janela termina no sábado, 17/10


class TestJanela:
    def test_janela_de_tres_dias(self) -> None:
        assert JANELA_DIAS == 3
        assert limite(HOJE) == date(2026, 10, 17)

    def test_limite_na_virada_de_ano(self) -> None:
        assert limite(date(2026, 12, 30)) == date(2027, 1, 2)

    @pytest.mark.parametrize("dias", [1, 30])
    def test_antes_de_hoje_esta_atrasado(self, dias: int) -> None:
        assert situacao(HOJE - timedelta(days=dias), HOJE) == "atrasado"

    @pytest.mark.parametrize("dias", [0, 1, 3])
    def test_de_hoje_ate_hoje_mais_tres_esta_a_vencer(self, dias: int) -> None:
        assert situacao(HOJE + timedelta(days=dias), HOJE) == "a_vencer"

    def test_hoje_mais_quatro_fica_fora(self) -> None:
        assert situacao(HOJE + timedelta(days=4), HOJE) is None

    def test_virada_de_mes(self) -> None:
        assert situacao(date(2026, 11, 2), date(2026, 10, 30)) == "a_vencer"
        assert situacao(date(2026, 10, 31), date(2026, 11, 1)) == "atrasado"


class TestContar:
    def test_soma_por_origem_e_situacao(self) -> None:
        contagem = contar(
            [
                ("conta", "atrasado"),
                ("conta", "a_vencer"),
                ("conta", "a_vencer"),
                ("valor", "atrasado"),
                ("livre", "a_vencer"),
            ]
        )
        assert contagem == Contagem(
            contas=Total(atrasados=1, a_vencer=2),
            valores=Total(atrasados=1, a_vencer=0),
            livres=Total(atrasados=0, a_vencer=1),
        )
        assert contagem.total == 5

    def test_vazio(self) -> None:
        assert contar([]).total == 0


def _resumo(**totais: Total) -> Mensagem | None:
    return texto_resumo(Contagem(**totais), HOJE)


class TestTextoResumo:
    def test_sem_nada_nao_ha_mensagem(self) -> None:
        assert _resumo() is None

    def test_titulo_fixo(self) -> None:
        mensagem = _resumo(contas=Total(a_vencer=1))
        assert mensagem is not None
        assert mensagem.titulo == "Gerencia"

    def test_exemplo_contas_a_vencer_e_valor_atrasado(self) -> None:
        mensagem = _resumo(contas=Total(a_vencer=2), valores=Total(atrasados=1))
        assert mensagem is not None
        assert mensagem.corpo == "2 contas a pagar até sábado · 1 valor a receber, atrasado."

    def test_exemplo_contas_com_atrasada_e_lembrete(self) -> None:
        mensagem = _resumo(contas=Total(atrasados=1, a_vencer=2), livres=Total(a_vencer=1))
        assert mensagem is not None
        assert mensagem.corpo == "3 contas a pagar até sábado (1 atrasada) · 1 lembrete até sábado."

    @pytest.mark.parametrize(
        ("totais", "corpo"),
        [
            ({"contas": Total(atrasados=1)}, "1 conta a pagar, atrasada."),
            ({"contas": Total(atrasados=2)}, "2 contas a pagar, atrasadas."),
            ({"contas": Total(a_vencer=1)}, "1 conta a pagar até sábado."),
            (
                {"contas": Total(atrasados=2, a_vencer=1)},
                "3 contas a pagar até sábado (2 atrasadas).",
            ),
            ({"valores": Total(a_vencer=1)}, "1 valor a receber até sábado."),
            ({"valores": Total(atrasados=2)}, "2 valores a receber, atrasados."),
            (
                {"valores": Total(atrasados=1, a_vencer=1)},
                "2 valores a receber até sábado (1 atrasado).",
            ),
            ({"livres": Total(atrasados=1)}, "1 lembrete, atrasado."),
            ({"livres": Total(a_vencer=3)}, "3 lembretes até sábado."),
            ({"livres": Total(atrasados=2, a_vencer=1)}, "3 lembretes até sábado (2 atrasados)."),
        ],
    )
    def test_singular_plural_e_sufixos(self, totais: dict[str, Total], corpo: str) -> None:
        mensagem = _resumo(**totais)
        assert mensagem is not None
        assert mensagem.corpo == corpo

    def test_ordem_contas_valores_lembretes(self) -> None:
        mensagem = _resumo(
            livres=Total(a_vencer=1), valores=Total(a_vencer=1), contas=Total(a_vencer=1)
        )
        assert mensagem is not None
        assert mensagem.corpo == (
            "1 conta a pagar até sábado · 1 valor a receber até sábado · 1 lembrete até sábado."
        )

    @pytest.mark.parametrize(
        ("hoje", "dia"),
        [
            (date(2026, 10, 12), "quinta"),  # segunda → quinta
            (date(2026, 10, 13), "sexta"),
            (date(2026, 10, 15), "domingo"),
            (date(2026, 10, 16), "segunda"),
            (date(2026, 10, 17), "terça"),
            (date(2026, 10, 18), "quarta"),
        ],
    )
    def test_dia_da_semana_do_fim_da_janela_sem_feira(self, hoje: date, dia: str) -> None:
        mensagem = texto_resumo(Contagem(contas=Total(a_vencer=1)), hoje)
        assert mensagem is not None
        assert mensagem.corpo == f"1 conta a pagar até {dia}."

    def test_nunca_leva_valores_em_reais(self) -> None:
        mensagem = _resumo(
            contas=Total(atrasados=12, a_vencer=40),
            valores=Total(atrasados=3, a_vencer=7),
            livres=Total(atrasados=1, a_vencer=2),
        )
        assert mensagem is not None
        assert "R$" not in mensagem.corpo
        assert not any(
            c.isdigit() and mensagem.corpo[i + 1 : i + 2] == ","
            for i, c in enumerate(mensagem.corpo)
        )
