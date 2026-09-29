from collections.abc import Callable

from fastapi.testclient import TestClient

from app.models import Usuario


def test_health_responde_ok(client: TestClient) -> None:
    resposta = client.get("/health")
    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}


def test_me_sem_cookie_exige_login(client: TestClient) -> None:
    resposta = client.get("/api/v1/me")
    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "nao_autenticado"


def test_me_com_token_desconhecido_exige_login(client: TestClient) -> None:
    client.cookies.set("sessao", "token-inexistente")
    assert client.get("/api/v1/me").status_code == 401


def test_me_com_sessao_devolve_usuario(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, criar_usuario())
    resposta = client.get("/api/v1/me")
    assert resposta.status_code == 200
    assert resposta.json()["email"] == "ana@exemplo.com"


def test_rota_inexistente_usa_formato_de_erro(client: TestClient) -> None:
    resposta = client.get("/api/v1/nao-existe")
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "nao_encontrado"


def test_corpo_que_nao_e_json_e_recusado(client: TestClient) -> None:
    resposta = client.post(
        "/api/v1/auth/login",
        content="email=a&senha=b",
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resposta.status_code == 415
    assert resposta.json()["erro"]["codigo"] == "tipo_conteudo_invalido"
