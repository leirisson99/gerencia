from datetime import UTC, datetime, timedelta

from app.domain.login import calcular_bloqueio, sessao_expirada

AGORA = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
INICIO = datetime(2026, 9, 28, 11, 0, tzinfo=UTC)


def minutos(*valores: float) -> list[datetime]:
    return [INICIO + timedelta(minutes=v) for v in valores]


class TestCalcularBloqueio:
    def test_sem_falhas_nao_bloqueia(self) -> None:
        assert calcular_bloqueio([], AGORA) is None

    def test_quatro_falhas_nao_bloqueiam(self) -> None:
        assert calcular_bloqueio(minutos(0, 1, 2, 3), INICIO + timedelta(minutes=4)) is None

    def test_cinco_falhas_em_15_minutos_bloqueiam_ate_a_quinta_mais_15(self) -> None:
        falhas = minutos(0, 3, 6, 9, 12)
        agora = INICIO + timedelta(minutes=13)
        assert calcular_bloqueio(falhas, agora) == INICIO + timedelta(minutes=27)

    def test_ordem_das_falhas_nao_importa(self) -> None:
        falhas = minutos(12, 0, 9, 3, 6)
        agora = INICIO + timedelta(minutes=13)
        assert calcular_bloqueio(falhas, agora) == INICIO + timedelta(minutes=27)

    def test_cinco_falhas_espalhadas_em_20_minutos_nao_bloqueiam(self) -> None:
        falhas = minutos(0, 5, 10, 15, 20)
        assert calcular_bloqueio(falhas, INICIO + timedelta(minutes=21)) is None

    def test_quinta_falha_exatamente_15_minutos_depois_da_primeira_nao_bloqueia(self) -> None:
        falhas = minutos(0, 1, 2, 3, 15)
        assert calcular_bloqueio(falhas, INICIO + timedelta(minutes=16)) is None

    def test_bloqueio_vencido_libera(self) -> None:
        falhas = minutos(0, 1, 2, 3, 4)
        assert calcular_bloqueio(falhas, INICIO + timedelta(minutes=19)) is None

    def test_ultimo_instante_do_bloqueio_ainda_bloqueia(self) -> None:
        falhas = minutos(0, 1, 2, 3, 4)
        agora = INICIO + timedelta(minutes=18, seconds=59)
        assert calcular_bloqueio(falhas, agora) == INICIO + timedelta(minutes=19)

    def test_falhas_de_antes_do_fim_do_bloqueio_nao_contam_depois(self) -> None:
        # Bloqueio até 19 min; depois dele, só 4 falhas novas: sem novo bloqueio.
        falhas = minutos(0, 1, 2, 3, 4, 20, 21, 22, 23)
        assert calcular_bloqueio(falhas, INICIO + timedelta(minutes=24)) is None

    def test_cinco_falhas_novas_depois_do_bloqueio_bloqueiam_de_novo(self) -> None:
        falhas = minutos(0, 1, 2, 3, 4, 20, 21, 22, 23, 24)
        agora = INICIO + timedelta(minutes=25)
        assert calcular_bloqueio(falhas, agora) == INICIO + timedelta(minutes=39)


class TestSessaoExpirada:
    def test_uso_ha_menos_de_30_dias_e_valida(self) -> None:
        ultimo_uso = AGORA - timedelta(days=29, hours=23, minutes=59)
        assert sessao_expirada(ultimo_uso, AGORA) is False

    def test_uso_ha_exatamente_30_dias_expira(self) -> None:
        assert sessao_expirada(AGORA - timedelta(days=30), AGORA) is True

    def test_uso_ha_31_dias_expira(self) -> None:
        assert sessao_expirada(AGORA - timedelta(days=31), AGORA) is True

    def test_prazo_configuravel(self) -> None:
        assert sessao_expirada(AGORA - timedelta(days=2), AGORA, dias=1) is True
