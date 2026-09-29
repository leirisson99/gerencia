from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Usuario
from app.services.senha import verificar_senha
from tests.conftest import SENHA_PADRAO


@pytest.fixture
def ana_e_bia(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> tuple[Usuario, Usuario]:
    ana = criar_usuario()
    bia = criar_usuario(email="bia@exemplo.com", nome="Bia Lima", cargo="Designer")
    logar(client, ana)
    return ana, bia


def test_sessao_de_ana_so_le_ana(client: TestClient, ana_e_bia: tuple[Usuario, Usuario]) -> None:
    ana, _ = ana_e_bia
    corpo = client.get("/api/v1/me").json()
    assert corpo["id"] == ana.id
    assert "bia" not in client.get("/api/v1/me").text.lower()


def test_edicao_de_ana_nao_toca_em_bia(
    client: TestClient, ana_e_bia: tuple[Usuario, Usuario], db: Session
) -> None:
    ana, bia = ana_e_bia

    client.patch("/api/v1/me", json={"nome": "Ana Nova", "cargo": "CTO"})

    db.refresh(bia)
    db.refresh(ana)
    assert (bia.nome, bia.cargo) == ("Bia Lima", "Designer")
    assert (ana.nome, ana.cargo) == ("Ana Nova", "CTO")


def test_troca_de_senha_de_ana_nao_toca_em_bia(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    logar: Callable[[TestClient, Usuario], str],
    ana_e_bia: tuple[Usuario, Usuario],
    db: Session,
) -> None:
    _, bia = ana_e_bia
    cliente_bia = novo_client()
    logar(cliente_bia, bia)

    client.put("/api/v1/me/senha", json={"senha_atual": SENHA_PADRAO, "nova_senha": "outra789x"})

    db.refresh(bia)
    assert verificar_senha(bia.senha_hash, SENHA_PADRAO)
    assert cliente_bia.get("/api/v1/me").status_code == 200


def test_nao_ha_rota_que_receba_id_de_usuario(client: TestClient) -> None:
    # O usuário vem sempre da sessão; nenhuma rota aceita id de usuário no caminho.
    rotas = client.get("/openapi.json").json()["paths"]
    assert all("usuario" not in caminho for caminho in rotas)
