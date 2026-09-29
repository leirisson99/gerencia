import pytest

from app.domain.cartela import CasaGerada, Progresso, gerar_casas, progresso, quantidade_de_casas

REAL = 100  # centavos


def valores(casas: list[CasaGerada]) -> list[int]:
    return [c.valor for c in casas if not c.is_ajuste]


def ajuste(casas: list[CasaGerada]) -> int | None:
    extras = [c.valor for c in casas if c.is_ajuste]
    return extras[0] if extras else None


class TestGerarCasas:
    # Tabela do briefing.
    def test_meta_1378_base_1_fecha_sem_ajuste(self) -> None:
        casas = gerar_casas(1_378 * REAL, 1 * REAL)
        assert valores(casas) == [k * REAL for k in range(1, 53)]
        assert ajuste(casas) is None

    def test_meta_1000_base_1(self) -> None:
        casas = gerar_casas(1_000 * REAL, 1 * REAL)
        assert len(valores(casas)) == 44
        assert sum(valores(casas)) == 990 * REAL
        assert ajuste(casas) == 10 * REAL

    def test_meta_5000_base_1(self) -> None:
        casas = gerar_casas(5_000 * REAL, 1 * REAL)
        assert len(valores(casas)) == 99
        assert ajuste(casas) == 50 * REAL

    def test_meta_5000_base_5(self) -> None:
        casas = gerar_casas(5_000 * REAL, 5 * REAL)
        assert valores(casas) == [k * 5 * REAL for k in range(1, 45)]
        assert ajuste(casas) == 50 * REAL

    def test_ordem_sequencial_com_ajuste_por_ultimo(self) -> None:
        casas = gerar_casas(1_000 * REAL, 1 * REAL)
        assert [c.ordem for c in casas] == list(range(1, 46))
        assert casas[-1].is_ajuste
        assert not any(c.is_ajuste for c in casas[:-1])

    def test_meta_igual_a_base(self) -> None:
        assert gerar_casas(REAL, REAL) == [CasaGerada(ordem=1, valor=REAL, is_ajuste=False)]

    @pytest.mark.parametrize(
        ("meta", "base"), [(1, 1), (7, 3), (137_800, 100), (99_999, 7), (10_000_000, 100)]
    )
    def test_soma_e_sempre_a_meta_e_n_e_maximo(self, meta: int, base: int) -> None:
        casas = gerar_casas(meta, base)
        n = len(valores(casas))
        assert sum(c.valor for c in casas) == meta
        assert base * n * (n + 1) // 2 <= meta
        assert base * (n + 1) * (n + 2) // 2 > meta

    @pytest.mark.parametrize(("meta", "base"), [(99, 100), (0, 100), (100, 0)])
    def test_entradas_invalidas(self, meta: int, base: int) -> None:
        with pytest.raises(ValueError):
            gerar_casas(meta, base)


class TestProgresso:
    CASAS = [(44 * REAL, True), (43 * REAL, False), (10 * REAL, True), (1 * REAL, False)]

    def test_parcial(self) -> None:
        assert progresso(self.CASAS, 98 * REAL) == Progresso(
            guardado=54 * REAL, falta=44 * REAL, percentual=55, maior_casa_livre=43 * REAL
        )

    def test_nada_depositado(self) -> None:
        resultado = progresso([(REAL, False), (2 * REAL, False)], 3 * REAL)
        assert (resultado.guardado, resultado.percentual, resultado.maior_casa_livre) == (
            0,
            0,
            2 * REAL,
        )

    def test_completa(self) -> None:
        resultado = progresso([(REAL, True), (2 * REAL, True)], 3 * REAL)
        assert resultado == Progresso(
            guardado=3 * REAL, falta=0, percentual=100, maior_casa_livre=None
        )

    def test_percentual_arredonda_para_baixo(self) -> None:
        assert progresso([(1, True), (2, False)], 3).percentual == 33


@pytest.mark.parametrize(
    ("meta", "base", "esperado"),
    [(137_800, 100, 52), (100_000, 100, 45), (500_000, 500, 45), (100, 100, 1)],
)
def test_quantidade_de_casas_sem_gerar(meta: int, base: int, esperado: int) -> None:
    assert quantidade_de_casas(meta, base) == esperado == len(gerar_casas(meta, base))


def test_quantidade_de_casas_para_metas_enormes() -> None:
    assert quantidade_de_casas(99_999_999_999, 1) > 1_000
