import pytest

from app.domain.usuario import ciclo_pelo_mes, pode_ter_pj, verificar_pj


@pytest.mark.parametrize(
    ("tipo", "carteira", "esperado"),
    [
        ("prestador", "pf", True),
        ("clt", "pf", False),
        ("clt_prestador", "pf", False),
        ("prestador", "pj", True),
        ("clt_prestador", "pj", True),
        ("clt", "pj", True),
    ],
)
def test_pj_conta_sempre_pelo_mes(tipo: str, carteira: str, esperado: bool) -> None:
    assert ciclo_pelo_mes(tipo, carteira) is esperado


def test_sem_carteira_vale_pf() -> None:
    assert ciclo_pelo_mes("clt") is False
    assert ciclo_pelo_mes("prestador") is True


@pytest.mark.parametrize(
    ("tipo", "esperado"), [("clt", False), ("prestador", True), ("clt_prestador", True)]
)
def test_quem_pode_ter_pj(tipo: str, esperado: bool) -> None:
    assert pode_ter_pj(tipo) is esperado


class TestVerificarPj:
    def test_clt_nao_liga(self) -> None:
        assert verificar_pj(True, "clt", False) == "tipo_sem_pj"

    def test_quem_presta_servico_liga(self) -> None:
        assert verificar_pj(True, "prestador", False) is None
        assert verificar_pj(True, "clt_prestador", True) is None

    def test_desligar_com_dados(self) -> None:
        assert verificar_pj(False, "prestador", True) == "pj_com_dados"

    def test_desligar_sem_dados(self) -> None:
        assert verificar_pj(False, "prestador", False) is None

    def test_trocar_para_clt(self) -> None:
        assert verificar_pj(False, "clt", True) == "pj_com_dados"
        assert verificar_pj(False, "clt", False) is None
