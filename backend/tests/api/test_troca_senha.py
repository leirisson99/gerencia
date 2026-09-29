from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Usuario
from tests.conftest import SENHA_PADRAO

URL = "/api/v1/me/senha"
NOVA = "novaSenha456"


def trocar(client: TestClient, atual: str = SENHA_PADRAO, nova: str = NOVA):
    return client.put(URL, json={"senha_atual": atual, "nova_senha": nova})


def test_troca_a_senha_e_derruba_as_outras_sessoes(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    usuario = criar_usuario()
    logar(client, usuario)
    outro_navegador = novo_client()
    logar(outro_navegador, usuario)

    resposta = trocar(client)

    assert resposta.status_code == 204
    assert client.get("/api/v1/me").status_code == 200
    assert outro_navegador.get("/api/v1/me").status_code == 401


def test_entra_com_a_nova_senha_e_nao_com_a_antiga(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, criar_usuario())
    trocar(client)

    outro = novo_client()
    login = {"email": "ana@exemplo.com"}
    assert (
        outro.post("/api/v1/auth/login", json={**login, "senha": SENHA_PADRAO}).status_code == 401
    )
    assert outro.post("/api/v1/auth/login", json={**login, "senha": NOVA}).status_code == 200


def test_senha_atual_errada(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, criar_usuario())

    resposta = trocar(client, atual="errada123")

    assert resposta.status_code == 400
    assert resposta.json()["erro"]["codigo"] == "senha_atual_incorreta"


def test_nova_senha_fraca(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, criar_usuario())

    resposta = trocar(client, nova="abcdefgh")

    assert resposta.status_code == 422
    assert "nova_senha" in resposta.json()["erro"]["campos"]


def test_nova_senha_igual_a_atual(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, criar_usuario())

    resposta = trocar(client, nova=SENHA_PADRAO)

    assert resposta.status_code == 422
    assert "nova_senha" in resposta.json()["erro"]["campos"]


def test_troca_exige_login(client: TestClient) -> None:
    assert trocar(client).status_code == 401


def test_troca_obrigatoria_libera_so_troca_de_senha_e_logout(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    db: Session,
) -> None:
    usuario = criar_usuario()
    db.execute(update(Usuario).where(Usuario.id == usuario.id).values(troca_senha_obrigatoria=True))
    db.commit()

    login = client.post(
        "/api/v1/auth/login", json={"email": "ana@exemplo.com", "senha": SENHA_PADRAO}
    )
    assert login.status_code == 200
    assert login.json()["troca_senha_obrigatoria"] is True

    bloqueado = client.get("/api/v1/me")
    assert bloqueado.status_code == 403
    assert bloqueado.json()["erro"]["codigo"] == "troca_senha_obrigatoria"

    assert trocar(client).status_code == 204

    liberado = client.get("/api/v1/me")
    assert liberado.status_code == 200
    assert liberado.json()["troca_senha_obrigatoria"] is False


def test_logout_liberado_com_troca_obrigatoria(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, criar_usuario(troca_senha_obrigatoria=True))
    assert client.post("/api/v1/auth/logout").status_code == 204
