import pytest

from app import cli
from app.services.senha import verificar_senha


def digitar(monkeypatch: pytest.MonkeyPatch, *respostas: str) -> None:
    fila = list(respostas)
    monkeypatch.setattr(cli, "getpass", lambda _prompt="": fila.pop(0))


def test_hash_senha_imprime_um_hash_que_confere(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    digitar(monkeypatch, "segredoAdmin1", "segredoAdmin1")

    assert cli.main(["hash-senha"]) == 0

    saida = capsys.readouterr().out
    linha = next(linha for linha in saida.splitlines() if linha.startswith("ADMIN_SENHA_HASH="))
    hash_ = linha.removeprefix("ADMIN_SENHA_HASH=").strip("'")
    assert verificar_senha(hash_, "segredoAdmin1")
    assert "segredoAdmin1" not in saida


def test_hash_senha_recusa_confirmacao_diferente(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    digitar(monkeypatch, "segredoAdmin1", "segredoAdmin2")

    assert cli.main(["hash-senha"]) == 1
    assert "não conferem" in capsys.readouterr().err


def test_hash_senha_segue_a_regra_de_senha(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    digitar(monkeypatch, "curta", "curta")

    assert cli.main(["hash-senha"]) == 1
    assert "caracteres" in capsys.readouterr().err
