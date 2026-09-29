from datetime import date, timedelta

import pytest

from app.domain.ciclo import (
    Ciclo,
    ProblemaCobertura,
    ciclo_atual,
    ciclo_da_data,
    montar_ciclos,
    verificar_cobertura,
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
