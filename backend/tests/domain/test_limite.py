import pytest

from app.domain.limite import limite_permitido, piorou, situacao

LIMITE = 30_000  # R$ 300,00


@pytest.mark.parametrize(
    ("usado", "esperado"),
    [
        (0, "ok"),
        (23_999, "ok"),  # 79,99%
        (24_000, "atencao"),  # 80% exatos
        (29_999, "atencao"),
        (30_000, "atencao"),  # 100% exatos
        (30_001, "estourado"),  # 100,01%
        (90_000, "estourado"),
    ],
)
def test_situacao_nas_fronteiras(usado: int, esperado: str) -> None:
    assert situacao(usado, LIMITE) == esperado


def test_fronteira_de_80_por_cento_sem_arredondar() -> None:
    # 80% de 333 centavos = 266,4: 266 ainda é ok, 267 já é atenção.
    assert situacao(266, 333) == "ok"
    assert situacao(267, 333) == "atencao"


def test_limite_de_um_centavo() -> None:
    assert situacao(0, 1) == "ok"
    assert situacao(1, 1) == "atencao"
    assert situacao(2, 1) == "estourado"


@pytest.mark.parametrize(
    ("antes", "depois", "esperado"),
    [
        ("ok", "atencao", True),
        ("ok", "estourado", True),
        ("atencao", "estourado", True),
        ("ok", "ok", False),
        ("atencao", "atencao", False),
        ("estourado", "estourado", False),
        ("atencao", "ok", False),
        ("estourado", "atencao", False),
    ],
)
def test_piorou(antes: str, depois: str, esperado: bool) -> None:
    assert piorou(antes, depois) is esperado


def test_limite_so_em_categoria_de_saida() -> None:
    assert limite_permitido("saida") is True
    assert limite_permitido("entrada") is False
