from datetime import UTC, datetime, timedelta

from app.domain.atividade import (
    fatiar_pagina,
    limite_retencao,
    precisa_registrar_visita,
    tipo_edicao_lembrete,
)

AGORA = datetime(2026, 10, 2, 15, 0, tzinfo=UTC)


class TestPrecisaRegistrarVisita:
    def test_primeira_visita(self) -> None:
        assert precisa_registrar_visita(None, AGORA)

    def test_dentro_da_janela_nao_registra(self) -> None:
        assert not precisa_registrar_visita(AGORA - timedelta(minutes=29, seconds=59), AGORA)

    def test_trinta_minutos_depois_registra(self) -> None:
        assert precisa_registrar_visita(AGORA - timedelta(minutes=30), AGORA)


class TestLimiteRetencao:
    def test_doze_meses_antes(self) -> None:
        assert limite_retencao(AGORA) == datetime(2025, 10, 2, 15, 0, tzinfo=UTC)

    def test_29_de_fevereiro_vira_28(self) -> None:
        agora = datetime(2028, 2, 29, 10, 0, tzinfo=UTC)
        assert limite_retencao(agora) == datetime(2027, 2, 28, 10, 0, tzinfo=UTC)


class TestTipoEdicaoLembrete:
    def test_concluir(self) -> None:
        assert tipo_edicao_lembrete(False, True) == "lembrete_concluido"

    def test_reabrir_e_edicao_comum(self) -> None:
        assert tipo_edicao_lembrete(True, False) == "lembrete_editado"
        assert tipo_edicao_lembrete(False, False) == "lembrete_editado"
        assert tipo_edicao_lembrete(True, True) == "lembrete_editado"


class TestFatiarPagina:
    def test_com_mais_itens(self) -> None:
        assert fatiar_pagina([5, 4, 3], 2) == ([5, 4], True)

    def test_ultima_pagina(self) -> None:
        assert fatiar_pagina([2, 1], 2) == ([2, 1], False)
        assert fatiar_pagina([], 2) == ([], False)
