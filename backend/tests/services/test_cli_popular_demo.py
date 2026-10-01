from datetime import date

import pytest

from app import cli
from app.demo import ANA, CARLOS, Chamada, Conta, Popular


def popular_falso(criada: bool, usadas: list[tuple[str, str]]) -> Popular:
    def _popular(_api: Chamada, _hoje: date, senha: str, conta: Conta) -> bool:
        usadas.append((conta.email, senha))
        return criada

    return _popular


def test_cria_cada_conta_e_avisa_a_que_ja_existia(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    usadas: list[tuple[str, str]] = []
    monkeypatch.delenv("DEMO_SENHA", raising=False)
    monkeypatch.setattr(cli, "getpass", lambda _prompt="": "demoGerencia1")
    monkeypatch.setattr(
        cli,
        "PERSONAS",
        {
            "ana": (ANA, popular_falso(True, usadas)),
            "carlos": (CARLOS, popular_falso(False, usadas)),
        },
    )

    assert cli.main(["popular-demo"]) == 0

    assert usadas == [(ANA.email, "demoGerencia1"), (CARLOS.email, "demoGerencia1")]
    saida = capsys.readouterr().out
    assert f"{ANA.email}: criada" in saida
    assert f"{CARLOS.email}: já existia, pulei" in saida
    assert "demoGerencia1" not in saida


def test_so_uma_conta_com_sufixo_e_senha_do_ambiente(monkeypatch: pytest.MonkeyPatch) -> None:
    usadas: list[tuple[str, str]] = []
    monkeypatch.setenv("DEMO_SENHA", "senhaDoGravador1")
    monkeypatch.setattr(cli, "getpass", lambda _prompt="": pytest.fail("não deveria perguntar"))
    monkeypatch.setattr(
        cli,
        "PERSONAS",
        {
            "ana": (ANA, popular_falso(True, usadas)),
            "carlos": (CARLOS, popular_falso(True, usadas)),
        },
    )

    assert cli.main(["popular-demo", "--so", "ana", "--sufixo", "v04"]) == 0

    assert usadas == [("ana.demo+v04@exemplo.com", "senhaDoGravador1")]


def test_senha_fraca_para_antes_de_chamar_a_api(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.delenv("DEMO_SENHA", raising=False)
    monkeypatch.setattr(cli, "getpass", lambda _prompt="": "123")
    monkeypatch.setattr(cli, "PERSONAS", {})

    assert cli.main(["popular-demo"]) == 1
    assert capsys.readouterr().err
