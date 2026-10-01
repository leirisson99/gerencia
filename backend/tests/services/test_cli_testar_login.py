from collections.abc import Callable
from typing import Any

import pytest

from app import cli

LOGIN_ADMIN = {"papel": "admin", "troca_senha_obrigatoria": False}


def preparar(
    monkeypatch: pytest.MonkeyPatch, respostas: dict[str, tuple[int, dict[str, Any]]]
) -> list[tuple[str, str, Any]]:
    """Senha digitada e API falsa; devolve as chamadas feitas, na ordem."""
    chamadas: list[tuple[str, str, Any]] = []

    def requisitar(
        _abrir: Callable[..., Any], metodo: str, url: str, corpo: Any = None
    ) -> tuple[int, dict[str, Any]]:
        chamadas.append((metodo, url, corpo))
        return respostas.get(url.removeprefix("http://localhost:8000"), (204, {}))

    monkeypatch.setattr(cli, "getpass", lambda _prompt="": "segredoAdmin1")
    monkeypatch.setattr(cli, "_requisitar", requisitar)
    return chamadas


def test_login_do_admin_confere_o_painel_e_sai(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    chamadas = preparar(
        monkeypatch,
        {"/api/v1/auth/login": (200, LOGIN_ADMIN), "/api/v1/admin/resumo": (200, {})},
    )

    assert cli.main(["testar-login", "Admin@Exemplo.com"]) == 0

    assert [(m, u.removeprefix("http://localhost:8000")) for m, u, _ in chamadas] == [
        ("POST", "/api/v1/auth/login"),
        ("GET", "/api/v1/admin/resumo"),
        ("POST", "/api/v1/auth/logout"),
    ]
    assert chamadas[0][2] == {"email": "Admin@Exemplo.com", "senha": "segredoAdmin1"}
    saida = capsys.readouterr().out
    assert "Login ok" in saida
    assert "papel: admin" in saida
    assert "Painel do administrador: 200" in saida
    assert "segredoAdmin1" not in saida


def test_login_recusado_mostra_a_mensagem_da_api(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    erro = {"erro": {"codigo": "credenciais_invalidas", "mensagem": "E-mail ou senha inválidos."}}
    chamadas = preparar(monkeypatch, {"/api/v1/auth/login": (401, erro)})

    assert cli.main(["testar-login", "admin@exemplo.com"]) == 1

    assert len(chamadas) == 1
    saida = capsys.readouterr().out
    assert "401" in saida
    assert "E-mail ou senha inválidos." in saida


def test_usuario_comum_nao_testa_o_painel(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    resposta = {"papel": "usuario", "troca_senha_obrigatoria": False}
    chamadas = preparar(monkeypatch, {"/api/v1/auth/login": (200, resposta)})

    assert cli.main(["testar-login", "ana@exemplo.com", "--api", "http://localhost:8000"]) == 0

    assert "/api/v1/admin/resumo" not in [u for _, u, _ in chamadas]
    assert "papel: usuario" in capsys.readouterr().out


def test_api_fora_do_ar(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    def fora(*_: Any, **__: Any) -> tuple[int, dict[str, Any]]:
        raise OSError("connection refused")

    monkeypatch.setattr(cli, "getpass", lambda _prompt="": "segredoAdmin1")
    monkeypatch.setattr(cli, "_requisitar", fora)

    assert cli.main(["testar-login", "admin@exemplo.com"]) == 1
    assert "Não foi possível falar com a API" in capsys.readouterr().err
