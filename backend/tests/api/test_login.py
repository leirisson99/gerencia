from collections.abc import Callable
from datetime import timedelta

from fastapi.testclient import TestClient
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models import Sessao, TentativaLogin, Usuario
from tests.conftest import SENHA_PADRAO, RelogioFixo

URL = "/api/v1/auth/login"


def logar_com(client: TestClient, email: str = "ana@exemplo.com", senha: str = SENHA_PADRAO):
    return client.post(URL, json={"email": email, "senha": senha})


def test_entra_com_email_e_senha_corretos(
    client: TestClient, criar_usuario: Callable[..., Usuario]
) -> None:
    criar_usuario()

    resposta = logar_com(client)

    assert resposta.status_code == 200
    assert resposta.json()["email"] == "ana@exemplo.com"
    assert "sessao" in resposta.cookies
    assert client.get("/api/v1/me").status_code == 200


def test_email_e_normalizado_no_login(
    client: TestClient, criar_usuario: Callable[..., Usuario]
) -> None:
    criar_usuario()
    assert logar_com(client, email="  ANA@Exemplo.com ").status_code == 200


def test_senha_errada_e_email_inexistente_tem_a_mesma_resposta(
    client: TestClient, criar_usuario: Callable[..., Usuario]
) -> None:
    criar_usuario()

    senha_errada = logar_com(client, senha="errada123")
    email_inexistente = logar_com(client, email="ninguem@exemplo.com")

    assert senha_errada.status_code == email_inexistente.status_code == 401
    assert senha_errada.json() == email_inexistente.json()
    assert senha_errada.json()["erro"]["codigo"] == "credenciais_invalidas"
    assert "sessao" not in senha_errada.cookies


def test_cinco_falhas_bloqueiam_mesmo_com_a_senha_certa(
    client: TestClient, criar_usuario: Callable[..., Usuario], relogio: RelogioFixo
) -> None:
    criar_usuario()
    for _ in range(5):
        relogio.avancar(minutes=1)
        assert logar_com(client, senha="errada123").status_code == 401

    resposta = logar_com(client)

    assert resposta.status_code == 429
    assert resposta.json()["erro"]["codigo"] == "login_bloqueado"
    assert int(resposta.headers["retry-after"]) == 15 * 60


def test_bloqueio_vale_para_email_inexistente(
    client: TestClient, criar_usuario: Callable[..., Usuario], relogio: RelogioFixo
) -> None:
    criar_usuario()
    for email in ("ana@exemplo.com", "ninguem@exemplo.com"):
        for _ in range(5):
            logar_com(client, email=email, senha="errada123")
    bloqueado_existente = logar_com(client)
    bloqueado_inexistente = logar_com(client, email="ninguem@exemplo.com")

    assert bloqueado_existente.status_code == bloqueado_inexistente.status_code == 429
    assert bloqueado_existente.json() == bloqueado_inexistente.json()


def test_bloqueio_de_um_email_nao_afeta_outro(
    client: TestClient, criar_usuario: Callable[..., Usuario]
) -> None:
    criar_usuario()
    criar_usuario(email="bia@exemplo.com")
    for _ in range(5):
        logar_com(client, senha="errada123")

    assert logar_com(client, email="bia@exemplo.com").status_code == 200


def test_entra_depois_que_o_bloqueio_vence(
    client: TestClient, criar_usuario: Callable[..., Usuario], relogio: RelogioFixo
) -> None:
    criar_usuario()
    for _ in range(5):
        logar_com(client, senha="errada123")
    relogio.avancar(minutes=15)

    assert logar_com(client).status_code == 200


def test_login_certo_zera_as_falhas(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    db: Session,
) -> None:
    criar_usuario()
    for _ in range(4):
        logar_com(client, senha="errada123")
    assert logar_com(client).status_code == 200

    total = db.scalar(select(func.count()).select_from(TentativaLogin))
    assert total == 0
    for _ in range(4):
        logar_com(client, senha="errada123")
    assert logar_com(client).status_code == 200


def test_falhas_com_mais_de_24_horas_sao_apagadas(
    client: TestClient, db: Session, relogio: RelogioFixo
) -> None:
    logar_com(client, email="ninguem@exemplo.com", senha="errada123")
    relogio.avancar(hours=25)
    logar_com(client, email="outro@exemplo.com", senha="errada123")

    emails = db.scalars(select(TentativaLogin.email_normalizado)).all()
    assert emails == ["outro@exemplo.com"]


def test_campos_faltando_no_login(client: TestClient) -> None:
    resposta = client.post(URL, json={"email": "ana@exemplo.com"})
    assert resposta.status_code == 422
    assert "senha" in resposta.json()["erro"]["campos"]


def test_logout_encerra_a_sessao(
    client: TestClient, criar_usuario: Callable[..., Usuario], db: Session
) -> None:
    criar_usuario()
    logar_com(client)

    resposta = client.post("/api/v1/auth/logout")

    assert resposta.status_code == 204
    assert "sessao" not in client.cookies
    assert db.scalar(select(func.count()).select_from(Sessao)) == 0
    assert client.get("/api/v1/me").status_code == 401


def test_logout_sem_sessao_exige_login(client: TestClient) -> None:
    resposta = client.post("/api/v1/auth/logout")
    assert resposta.status_code == 401
    assert resposta.json()["erro"]["codigo"] == "nao_autenticado"


def test_sessao_sem_uso_por_30_dias_expira(
    client: TestClient, criar_usuario: Callable[..., Usuario], relogio: RelogioFixo
) -> None:
    criar_usuario()
    logar_com(client)
    relogio.avancar(days=30)

    assert client.get("/api/v1/me").status_code == 401


def test_uso_renova_a_sessao_e_o_cookie(
    client: TestClient, criar_usuario: Callable[..., Usuario], relogio: RelogioFixo, db: Session
) -> None:
    criar_usuario()
    logar_com(client)
    relogio.avancar(days=20)

    resposta = client.get("/api/v1/me")
    assert resposta.status_code == 200
    assert "max-age=2592000" in resposta.headers["set-cookie"].lower()

    relogio.avancar(days=20)  # 40 dias desde o login, 20 desde o último uso
    assert client.get("/api/v1/me").status_code == 200


def test_sessao_de_outro_usuario_nao_e_afetada_pelo_logout(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
    db: Session,
) -> None:
    ana = criar_usuario()
    bia = criar_usuario(email="bia@exemplo.com")
    logar(client, ana)
    outro = novo_client()
    logar(outro, bia)

    client.post("/api/v1/auth/logout")

    assert outro.get("/api/v1/me").json()["email"] == "bia@exemplo.com"


def test_hash_antigo_e_refeito_no_login(
    client: TestClient, criar_usuario: Callable[..., Usuario], db: Session
) -> None:
    from argon2 import PasswordHasher

    usuario = criar_usuario()
    hash_fraco = PasswordHasher(time_cost=1, memory_cost=8192).hash(SENHA_PADRAO)
    db.execute(update(Usuario).where(Usuario.id == usuario.id).values(senha_hash=hash_fraco))
    db.commit()

    assert logar_com(client).status_code == 200
    db.refresh(usuario)
    assert usuario.senha_hash != hash_fraco


def test_cada_uso_atualiza_o_ultimo_uso_da_sessao(
    client: TestClient, criar_usuario: Callable[..., Usuario], relogio: RelogioFixo, db: Session
) -> None:
    criar_usuario()
    logar_com(client)
    login_em = relogio.agora
    assert db.scalar(select(Sessao.ultimo_uso_em)) == login_em

    relogio.avancar(minutes=5)
    client.get("/api/v1/me")

    assert db.scalar(select(Sessao.ultimo_uso_em)) == login_em + timedelta(minutes=5)
