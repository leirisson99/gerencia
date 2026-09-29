import pytest

from app.domain.categoria import edicao_permitida


@pytest.mark.parametrize(
    ("muda_nome", "desativa"), [(False, False), (True, False), (False, True), (True, True)]
)
def test_categoria_comum_pode_tudo(muda_nome: bool, desativa: bool) -> None:
    assert edicao_permitida(e_salario=False, muda_nome=muda_nome, desativa=desativa)


def test_salario_nao_muda_de_nome() -> None:
    assert not edicao_permitida(e_salario=True, muda_nome=True, desativa=False)


def test_salario_nao_e_desativada() -> None:
    assert not edicao_permitida(e_salario=True, muda_nome=False, desativa=True)


def test_salario_sem_mudanca_efetiva_e_permitido() -> None:
    # Ex.: enviar o mesmo nome ou ativa=true não altera nada.
    assert edicao_permitida(e_salario=True, muda_nome=False, desativa=False)
