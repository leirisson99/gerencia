"""Feature 015: ativar e desativar as notificações num aparelho."""

from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import InscricaoPush, Usuario

CHAVE = "/api/v1/push/chave"
INSCRICAO = "/api/v1/push/inscricao"
ENDPOINT = "https://fcm.googleapis.com/fcm/send/abc123"


@pytest.fixture
def com_chaves(settings_teste: Settings) -> None:
    settings_teste.vapid_chave_publica = "BPublicaDeTeste"
    settings_teste.vapid_chave_privada = "privada-de-teste"
    settings_teste.vapid_contato = "mailto:admin@exemplo.com"


@pytest.fixture
def ana(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> Usuario:
    usuario = criar_usuario()
    logar(client, usuario)
    return usuario


def inscricao(endpoint: str = ENDPOINT, **extra: Any) -> dict[str, Any]:
    return {"endpoint": endpoint, "keys": {"p256dh": "p" * 87, "auth": "a" * 22}, **extra}


def inscricoes(db: Session) -> list[tuple[int, str, str]]:
    return [
        (i.usuario_id, i.endpoint, i.p256dh)
        for i in db.scalars(select(InscricaoPush).order_by(InscricaoPush.id))
    ]


# --- chave pública ---------------------------------------------------------------------------


@pytest.mark.usefixtures("com_chaves")
def test_chave_publica(client: TestClient, ana: Usuario) -> None:
    resposta = client.get(CHAVE)

    assert resposta.status_code == 200
    assert resposta.json() == {"chave_publica": "BPublicaDeTeste"}


def test_sem_chaves_push_indisponivel(client: TestClient, ana: Usuario) -> None:
    for resposta in (client.get(CHAVE), client.put(INSCRICAO, json=inscricao())):
        assert resposta.status_code == 503
        assert resposta.json()["erro"]["codigo"] == "push_indisponivel"


def test_exige_sessao(client: TestClient) -> None:
    assert client.get(CHAVE).status_code == 401
    assert client.put(INSCRICAO, json=inscricao()).status_code == 401
    assert client.request("DELETE", INSCRICAO, json={"endpoint": ENDPOINT}).status_code == 401


# --- inscrever -------------------------------------------------------------------------------


@pytest.mark.usefixtures("com_chaves")
def test_inscreve_o_aparelho(client: TestClient, ana: Usuario, db: Session) -> None:
    # US3.1
    resposta = client.put(INSCRICAO, json=inscricao(expirationTime=None))

    assert resposta.status_code == 204
    assert inscricoes(db) == [(ana.id, ENDPOINT, "p" * 87)]


@pytest.mark.usefixtures("com_chaves")
def test_inscrever_de_novo_atualiza_sem_duplicar(
    client: TestClient, ana: Usuario, db: Session
) -> None:
    client.put(INSCRICAO, json=inscricao())
    novas = {"endpoint": ENDPOINT, "keys": {"p256dh": "q" * 87, "auth": "b" * 22}}

    assert client.put(INSCRICAO, json=novas).status_code == 204
    assert inscricoes(db) == [(ana.id, ENDPOINT, "q" * 87)]


@pytest.mark.usefixtures("com_chaves")
def test_varios_aparelhos(client: TestClient, ana: Usuario, db: Session) -> None:
    client.put(INSCRICAO, json=inscricao())
    client.put(INSCRICAO, json=inscricao("https://updates.push.services.mozilla.com/wpush/v2/x"))

    assert len(inscricoes(db)) == 2


@pytest.mark.usefixtures("com_chaves")
def test_aparelho_de_outra_conta_passa_para_quem_ativou(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    ana: Usuario,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
    db: Session,
) -> None:
    # US3.6, FR-008: um aparelho recebe o resumo de um único usuário
    outro = novo_client()
    bia = criar_usuario(email="bia@exemplo.com")
    logar(outro, bia)
    outro.put(INSCRICAO, json=inscricao())

    assert client.put(INSCRICAO, json=inscricao()).status_code == 204
    assert inscricoes(db) == [(ana.id, ENDPOINT, "p" * 87)]


@pytest.mark.usefixtures("com_chaves")
@pytest.mark.parametrize(
    "corpo",
    [
        inscricao("http://push.exemplo/x"),
        inscricao("https://push.exemplo/" + "x" * 2048),
        {"endpoint": ENDPOINT},
        {"endpoint": ENDPOINT, "keys": {"p256dh": "p" * 87}},
        inscricao(extra="campo"),
    ],
    ids=["http", "longo", "sem_keys", "sem_auth", "campo_extra"],
)
def test_validacao(client: TestClient, ana: Usuario, db: Session, corpo: dict[str, Any]) -> None:
    resposta = client.put(INSCRICAO, json=corpo)

    assert resposta.status_code == 422
    assert resposta.json()["erro"]["codigo"] == "validacao"
    assert inscricoes(db) == []


# --- remover ---------------------------------------------------------------------------------


@pytest.mark.usefixtures("com_chaves")
def test_desativa_o_aparelho(client: TestClient, ana: Usuario, db: Session) -> None:
    # US3.3
    client.put(INSCRICAO, json=inscricao())
    client.put(INSCRICAO, json=inscricao("https://push.exemplo/outro"))

    resposta = client.request("DELETE", INSCRICAO, json={"endpoint": ENDPOINT})

    assert resposta.status_code == 204
    assert inscricoes(db) == [(ana.id, "https://push.exemplo/outro", "p" * 87)]


def test_remover_funciona_mesmo_sem_chaves(client: TestClient, ana: Usuario, db: Session) -> None:
    # Sair da conta precisa limpar o aparelho mesmo com o push desligado.
    db.add(InscricaoPush(usuario_id=ana.id, endpoint=ENDPOINT, p256dh="p", auth="a"))
    db.commit()

    assert client.request("DELETE", INSCRICAO, json={"endpoint": ENDPOINT}).status_code == 204
    assert inscricoes(db) == []


def test_remover_inexistente_e_404(client: TestClient, ana: Usuario) -> None:
    resposta = client.request("DELETE", INSCRICAO, json={"endpoint": ENDPOINT})

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "nao_encontrado"


@pytest.mark.usefixtures("com_chaves")
def test_nao_remove_aparelho_de_outro_usuario(
    client: TestClient,
    ana: Usuario,
    criar_usuario: Callable[..., Usuario],
    db: Session,
) -> None:
    bia = criar_usuario(email="bia@exemplo.com")
    db.add(InscricaoPush(usuario_id=bia.id, endpoint=ENDPOINT, p256dh="p", auth="a"))
    db.commit()

    resposta = client.request("DELETE", INSCRICAO, json={"endpoint": ENDPOINT})

    assert resposta.status_code == 404
    assert inscricoes(db) == [(bia.id, ENDPOINT, "p")]
