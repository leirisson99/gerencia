from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from httpx import Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AcaoAdmin, Usuario
from tests.api.conftest import USUARIOS
from tests.conftest import SENHA_PADRAO, RelogioFixo

LOGIN = "/api/v1/auth/login"


def desativar(cliente: TestClient, usuario_id: int) -> Response:
    return cliente.post(f"{USUARIOS}/{usuario_id}/desativar")


def reativar(cliente: TestClient, usuario_id: int) -> Response:
    return cliente.post(f"{USUARIOS}/{usuario_id}/reativar")


def entrar(cliente: TestClient, email: str, senha: str = SENHA_PADRAO) -> Response:
    return cliente.post(LOGIN, json={"email": email, "senha": senha})


# --- Desativar -----------------------------------------------------------------------------


def test_desativar_derruba_sessoes_e_marca_a_conta(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    novo_client: Callable[[], TestClient],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    cliente_ana = novo_client()
    logar(cliente_ana, usuarios["ana"])

    resposta = desativar(cliente_admin, usuarios["ana"].id)

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False
    assert set(resposta.json()) == {"id", "nome", "email", "criado_em", "ativo"}
    assert cliente_ana.get("/api/v1/me").status_code == 401


def test_conta_desativada_nao_entra_com_a_senha_certa(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], novo_client: Callable[[], TestClient]
) -> None:
    desativar(cliente_admin, usuarios["ana"].id)

    resposta = entrar(novo_client(), "ana@exemplo.com")

    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "conta_desativada"
    assert "sessao" not in resposta.cookies


def test_conta_desativada_com_senha_errada_nao_revela_a_situacao(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], novo_client: Callable[[], TestClient]
) -> None:
    desativar(cliente_admin, usuarios["ana"].id)

    resposta = entrar(novo_client(), "ana@exemplo.com", "senhaErrada1")

    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "credenciais_invalidas"


def test_sessao_que_escapou_da_limpeza_e_recusada(
    client: TestClient,
    usuarios: dict[str, Usuario],
    logar: Callable[[TestClient, Usuario], str],
    db: Session,
) -> None:
    logar(client, usuarios["ana"])
    usuarios["ana"].ativo = False
    db.commit()

    assert client.get("/api/v1/me").status_code == 401


def test_desativar_fica_registrado(
    cliente_admin: TestClient, admin: Usuario, usuarios: dict[str, Usuario], db: Session
) -> None:
    desativar(cliente_admin, usuarios["bia"].id)

    acoes = db.scalars(select(AcaoAdmin)).all()

    assert [(a.admin_id, a.acao, a.usuario_alvo_id) for a in acoes] == [
        (admin.id, "desativar_conta", usuarios["bia"].id)
    ]


def test_desativar_de_novo_nao_muda_nada(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], db: Session
) -> None:
    desativar(cliente_admin, usuarios["bia"].id)
    resposta = desativar(cliente_admin, usuarios["bia"].id)

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is False
    assert len(db.scalars(select(AcaoAdmin)).all()) == 1


def test_desativar_nao_derruba_o_admin(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], relogio: RelogioFixo
) -> None:
    desativar(cliente_admin, usuarios["ana"].id)
    relogio.avancar(seconds=1)
    assert cliente_admin.get(USUARIOS).status_code == 200


# --- Reativar ------------------------------------------------------------------------------


def test_reativar_devolve_o_acesso_com_a_mesma_senha(
    cliente_admin: TestClient,
    admin: Usuario,
    usuarios: dict[str, Usuario],
    novo_client: Callable[[], TestClient],
    db: Session,
) -> None:
    desativar(cliente_admin, usuarios["ana"].id)

    resposta = reativar(cliente_admin, usuarios["ana"].id)

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is True
    assert entrar(novo_client(), "ana@exemplo.com").status_code == 200
    acoes = [a.acao for a in db.scalars(select(AcaoAdmin).order_by(AcaoAdmin.id))]
    assert acoes == ["desativar_conta", "reativar_conta"]


def test_reativar_conta_ativa_nao_registra(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], db: Session
) -> None:
    resposta = reativar(cliente_admin, usuarios["ana"].id)

    assert resposta.status_code == 200
    assert resposta.json()["ativo"] is True
    assert db.scalars(select(AcaoAdmin)).all() == []


def test_reset_de_conta_desativada_nao_libera_o_login(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], novo_client: Callable[[], TestClient]
) -> None:
    desativar(cliente_admin, usuarios["ana"].id)
    senha = cliente_admin.post(f"{USUARIOS}/{usuarios['ana'].id}/reset-senha").json()[
        "senha_temporaria"
    ]

    assert entrar(novo_client(), "ana@exemplo.com", senha).status_code == 403


# --- Acesso e alvos inválidos --------------------------------------------------------------


@pytest.mark.parametrize("acao", [desativar, reativar])
def test_conta_inexistente_ou_do_admin(
    cliente_admin: TestClient, admin: Usuario, acao: Callable[[TestClient, int], Response]
) -> None:
    for alvo in (999_999_999, admin.id):
        resposta = acao(cliente_admin, alvo)
        assert resposta.status_code == 404


@pytest.mark.parametrize("acao", [desativar, reativar])
def test_usuario_comum_nao_desativa_nem_reativa(
    client: TestClient,
    usuarios: dict[str, Usuario],
    logar: Callable[[TestClient, Usuario], str],
    db: Session,
    acao: Callable[[TestClient, int], Response],
) -> None:
    logar(client, usuarios["ana"])

    resposta = acao(client, usuarios["bia"].id)

    assert resposta.status_code == 403
    db.refresh(usuarios["bia"])
    assert usuarios["bia"].ativo is True


# --- Filtro da lista -----------------------------------------------------------------------


@pytest.mark.parametrize(
    ("situacao", "esperado"),
    [
        (None, ["ana@exemplo.com", "bia@exemplo.com", "caio@exemplo.com"]),
        ("ativos", ["ana@exemplo.com", "caio@exemplo.com"]),
        ("desativados", ["bia@exemplo.com"]),
    ],
)
def test_filtra_pela_situacao(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    situacao: str | None,
    esperado: list[str],
) -> None:
    desativar(cliente_admin, usuarios["bia"].id)
    params = {"situacao": situacao} if situacao else {}

    corpo = cliente_admin.get(USUARIOS, params=params).json()

    assert [u["email"] for u in corpo] == esperado


def test_situacao_invalida(cliente_admin: TestClient) -> None:
    assert cliente_admin.get(USUARIOS, params={"situacao": "todos"}).status_code == 422
