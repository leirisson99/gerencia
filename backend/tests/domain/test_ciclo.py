from datetime import date, timedelta

import pytest

from app.domain.ciclo import (
    Ciclo,
    ProblemaCobertura,
    ProblemaTroca,
    ciclo_atual,
    ciclo_da_data,
    ciclo_mensal,
    montar_ciclos,
    verificar_cobertura,
    verificar_troca_tipo_renda,
)

OUT_05 = date(2026, 10, 5)
NOV_06 = date(2026, 11, 6)
DEZ_05 = date(2026, 12, 5)


class TestMontarCiclos:
    def test_sem_salario_nao_ha_ciclo(self) -> None:
        assert montar_ciclos([]) == []

    def test_um_salario_abre_um_ciclo_sem_fim(self) -> None:
        assert montar_ciclos([OUT_05]) == [
            Ciclo(inicio=OUT_05, fim=None, anterior=None, proximo=None)
        ]

    def test_segundo_salario_fecha_o_anterior_na_vespera(self) -> None:
        # US1.2: salários em 05/10 e 06/11 → 05/10 a 05/11 e aberto desde 06/11
        assert montar_ciclos([OUT_05, date(2026, 11, 6)]) == [
            Ciclo(inicio=OUT_05, fim=date(2026, 11, 5), anterior=None, proximo=NOV_06),
            Ciclo(inicio=NOV_06, fim=None, anterior=OUT_05, proximo=None),
        ]

    def test_ordem_das_datas_nao_importa(self) -> None:
        assert montar_ciclos([DEZ_05, OUT_05, NOV_06]) == montar_ciclos([OUT_05, NOV_06, DEZ_05])

    def test_dois_salarios_na_mesma_data_formam_um_ciclo(self) -> None:
        assert montar_ciclos([OUT_05, OUT_05]) == montar_ciclos([OUT_05])

    def test_ciclos_de_tamanhos_diferentes(self) -> None:
        ciclos = montar_ciclos([date(2026, 1, 1), date(2026, 1, 21), date(2026, 3, 2)])
        assert [(c.inicio, c.fim) for c in ciclos] == [
            (date(2026, 1, 1), date(2026, 1, 20)),  # 20 dias
            (date(2026, 1, 21), date(2026, 3, 1)),  # 40 dias
            (date(2026, 3, 2), None),
        ]

    def test_virada_de_ano(self) -> None:
        ciclos = montar_ciclos([date(2026, 12, 20), date(2027, 1, 20)])
        assert (ciclos[0].inicio, ciclos[0].fim) == (date(2026, 12, 20), date(2027, 1, 19))

    def test_ciclo_aberto(self) -> None:
        ciclos = montar_ciclos([OUT_05, NOV_06])
        assert [c.aberto for c in ciclos] == [False, True]


class TestCicloDaData:
    DATAS = [OUT_05, NOV_06, DEZ_05]

    def test_sem_salario(self) -> None:
        assert ciclo_da_data([], OUT_05) is None

    def test_data_antes_do_primeiro_salario(self) -> None:
        assert ciclo_da_data(self.DATAS, date(2026, 10, 4)) is None

    def test_data_do_salario_pertence_ao_ciclo_que_ele_abre(self) -> None:
        assert ciclo_da_data(self.DATAS, NOV_06).inicio == NOV_06

    def test_vespera_do_salario_pertence_ao_ciclo_anterior(self) -> None:
        assert ciclo_da_data(self.DATAS, date(2026, 11, 5)).inicio == OUT_05

    def test_ciclo_do_meio_com_vizinhos(self) -> None:
        # US3.2
        assert ciclo_da_data(self.DATAS, date(2026, 11, 20)) == Ciclo(
            inicio=NOV_06, fim=date(2026, 12, 4), anterior=OUT_05, proximo=DEZ_05
        )

    def test_data_distante_cai_no_ciclo_aberto(self) -> None:
        assert ciclo_da_data(self.DATAS, date(2030, 1, 1)).inicio == DEZ_05

    def test_toda_data_pertence_a_exatamente_um_ciclo(self) -> None:
        # SC-002: sem buracos nem sobreposição.
        datas = [date(2026, 1, 5), date(2026, 2, 3), date(2026, 2, 3), date(2026, 3, 31)]
        ciclos = montar_ciclos(datas)
        dia = date(2026, 1, 5)
        while dia <= date(2026, 12, 31):
            contem = [c for c in ciclos if c.inicio <= dia and (c.fim is None or dia <= c.fim)]
            assert len(contem) == 1, dia
            assert ciclo_da_data(datas, dia) == contem[0]
            dia += timedelta(days=1)


class TestCicloAtual:
    def test_sem_salario(self) -> None:
        assert ciclo_atual([]) is None

    def test_e_o_mais_recente(self) -> None:
        # US3.1
        assert ciclo_atual([OUT_05, DEZ_05, NOV_06]) == Ciclo(
            inicio=DEZ_05, fim=None, anterior=NOV_06, proximo=None
        )


class TestVerificarCobertura:
    def test_sem_lancamentos(self) -> None:
        assert verificar_cobertura([], None) is None

    def test_so_salarios(self) -> None:
        assert verificar_cobertura([OUT_05], None) is None

    def test_outros_lancamentos_sem_salario(self) -> None:
        assert verificar_cobertura([], OUT_05) is ProblemaCobertura.SEM_SALARIO

    @pytest.mark.parametrize("menor", [OUT_05, date(2026, 10, 6), date(2027, 1, 1)])
    def test_outros_a_partir_do_primeiro_salario(self, menor: date) -> None:
        assert verificar_cobertura([NOV_06, OUT_05], menor) is None

    def test_outro_lancamento_antes_do_primeiro_salario(self) -> None:
        resultado = verificar_cobertura([NOV_06, OUT_05], date(2026, 10, 4))
        assert resultado is ProblemaCobertura.ANTES_DO_PRIMEIRO_CICLO


class TestCicloMensal:
    """Ciclo do prestador: mês do calendário (US2)."""

    HOJE = date(2026, 10, 15)

    def test_mes_atual_aberto_sem_proximo(self) -> None:
        ciclo = ciclo_mensal(date(2026, 10, 15), self.HOJE, date(2026, 8, 3))
        assert ciclo == Ciclo(
            inicio=date(2026, 10, 1),
            fim=date(2026, 10, 31),
            anterior=date(2026, 9, 1),
            proximo=None,
            mes_atual=True,
        )
        assert ciclo.aberto

    def test_mes_passado_fechado_com_proximo(self) -> None:
        ciclo = ciclo_mensal(date(2026, 9, 10), self.HOJE, date(2026, 8, 3))
        assert ciclo == Ciclo(
            inicio=date(2026, 9, 1),
            fim=date(2026, 9, 30),
            anterior=date(2026, 8, 1),
            proximo=date(2026, 10, 1),
        )
        assert not ciclo.aberto

    def test_sem_anterior_quando_nao_ha_lancamento_antes(self) -> None:
        # US2.8: primeiro lançamento em agosto → agosto não tem anterior
        assert ciclo_mensal(date(2026, 8, 20), self.HOJE, date(2026, 8, 3)).anterior is None
        assert ciclo_mensal(date(2026, 8, 20), self.HOJE, date(2026, 8, 1)).anterior is None
        assert ciclo_mensal(date(2026, 8, 20), self.HOJE, None).anterior is None

    def test_anterior_com_lancamento_no_ultimo_dia_do_mes_anterior(self) -> None:
        ciclo = ciclo_mensal(date(2026, 8, 20), self.HOJE, date(2026, 7, 31))
        assert ciclo.anterior == date(2026, 7, 1)

    def test_mes_futuro_fechado_sem_proximo(self) -> None:
        ciclo = ciclo_mensal(date(2026, 12, 5), self.HOJE, None)
        assert ciclo.inicio == date(2026, 12, 1)
        assert ciclo.fim == date(2026, 12, 31)
        assert ciclo.proximo is None
        assert not ciclo.aberto

    @pytest.mark.parametrize(
        ("data", "fim"),
        [
            (date(2027, 2, 10), date(2027, 2, 28)),
            (date(2028, 2, 10), date(2028, 2, 29)),  # US2.5: bissexto
            (date(2026, 4, 30), date(2026, 4, 30)),
            (date(2026, 1, 1), date(2026, 1, 31)),
            (date(2026, 7, 31), date(2026, 7, 31)),
        ],
    )
    def test_fim_e_o_ultimo_dia_do_mes(self, data: date, fim: date) -> None:
        ciclo = ciclo_mensal(data, self.HOJE, None)
        assert ciclo.inicio == data.replace(day=1)
        assert ciclo.fim == fim

    def test_virada_de_ano(self) -> None:
        hoje = date(2027, 3, 1)
        dezembro = ciclo_mensal(date(2026, 12, 31), hoje, date(2026, 1, 1))
        assert dezembro.proximo == date(2027, 1, 1)
        janeiro = ciclo_mensal(date(2027, 1, 1), hoje, date(2026, 1, 1))
        assert janeiro.anterior == date(2026, 12, 1)
        assert janeiro.fim == date(2027, 1, 31)

    def test_dezembro_atual_sem_proximo(self) -> None:
        ciclo = ciclo_mensal(date(2026, 12, 1), date(2026, 12, 31), None)
        assert ciclo.aberto
        assert ciclo.proximo is None

    def test_ciclo_de_salario_continua_aberto_so_sem_fim(self) -> None:
        assert Ciclo(OUT_05, None, None, None).aberto
        assert not Ciclo(OUT_05, NOV_06, None, None).aberto


class TestTrocaTipoRenda:
    """US4: a troca nunca deixa lançamento fora de ciclo."""

    @pytest.mark.parametrize(
        ("atual", "novo"),
        [
            ("clt", "clt"),
            ("prestador", "prestador"),
            ("clt", "clt_prestador"),
            ("clt_prestador", "clt"),
            ("clt", "prestador"),
            ("clt_prestador", "prestador"),
        ],
    )
    def test_trocas_sempre_aceitas(self, atual: str, novo: str) -> None:
        # Mesmo com lançamentos que ficariam fora de um ciclo de salário.
        assert verificar_troca_tipo_renda(atual, novo, [], OUT_05, True) is None

    @pytest.mark.parametrize("novo", ["clt", "clt_prestador"])
    def test_prestador_sem_salario_com_lancamentos(self, novo: str) -> None:
        # US4.2
        resultado = verificar_troca_tipo_renda("prestador", novo, [], OUT_05, False)
        assert resultado is ProblemaTroca.LANCAMENTOS_SEM_CICLO

    def test_lancamento_antes_do_primeiro_salario(self) -> None:
        # US4.3
        resultado = verificar_troca_tipo_renda(
            "prestador", "clt", [date(2026, 9, 5)], date(2026, 9, 2), False
        )
        assert resultado is ProblemaTroca.LANCAMENTOS_SEM_CICLO

    def test_todos_os_lancamentos_cobertos(self) -> None:
        # US4.4: inclusive no mesmo dia do salário
        resultado = verificar_troca_tipo_renda(
            "prestador", "clt", [date(2026, 9, 5)], date(2026, 9, 5), False
        )
        assert resultado is None

    def test_sem_lancamento_nenhum(self) -> None:
        # US4.5
        assert verificar_troca_tipo_renda("prestador", "clt", [], None, False) is None

    def test_salario_irregular_tem_precedencia(self) -> None:
        # US4.6
        resultado = verificar_troca_tipo_renda("prestador", "clt_prestador", [], OUT_05, True)
        assert resultado is ProblemaTroca.SALARIO_INVALIDO

    @pytest.mark.parametrize("atual", ["prestador", "clt_prestador"])
    def test_servicos_pendentes_impedem_virar_clt(self, atual: str) -> None:
        # 013 US5.1, com precedência sobre os outros problemas
        resultado = verificar_troca_tipo_renda(
            atual, "clt", [], OUT_05, True, servicos_pendentes=True
        )
        assert resultado is ProblemaTroca.SERVICOS_PENDENTES

    @pytest.mark.parametrize(
        ("atual", "novo"), [("prestador", "clt_prestador"), ("clt_prestador", "prestador")]
    )
    def test_servicos_pendentes_nao_impedem_quem_continua_com_servicos(
        self, atual: str, novo: str
    ) -> None:
        resultado = verificar_troca_tipo_renda(
            atual, novo, [OUT_05], OUT_05, False, servicos_pendentes=True
        )
        assert resultado is None
