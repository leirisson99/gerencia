from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.models import AcaoAdmin, Usuario
from app.schemas.admin import DadosAdmin
from app.services.admin import criar_administrador
from tests.conftest import SENHA_PADRAO, RelogioFixo

USUARIOS = "/api/v1/admin/usuarios"


@pytest.fixture
def admin(db: Session, relogio: RelogioFixo) -> Usuario:
    usuario, _ = criar_administrador(
        db,
        DadosAdmin(nome="Admin", email="admin@exemplo.com", telefone="11987654321", cargo="Adm"),
        relogio.agora,
    )
    # Troca inicial já feita, para os testes irem direto às rotas.
    db.execute(
        update(Usuario).where(Usuario.id == usuario.id).values(troca_senha_obrigatoria=False)
    )
    db.commit()
    return usuario


@pytest.fixture
def cliente_admin(
    client: TestClient, admin: Usuario, logar: Callable[[TestClient, Usuario], str]
) -> TestClient:
    logar(client, admin)
    return client


@pytest.fixture
def usuarios(criar_usuario: Callable[..., Usuario], relogio: RelogioFixo) -> dict[str, Usuario]:
    caio = criar_usuario(email="caio@exemplo.com", nome="Caio Dias")
    relogio.avancar(minutes=1)
    ana = criar_usuario(email="ana@exemplo.com", nome="Ana Souza", cargo="Dev")
    bia = criar_usuario(email="bia@exemplo.com", nome="Bia Lima")
    return {"ana": ana, "bia": bia, "caio": caio}


def reset(cliente: TestClient, usuario_id: int):
    return cliente.post(f"{USUARIOS}/{usuario_id}/reset-senha")


def test_admin_ve_o_proprio_papel(cliente_admin: TestClient) -> None:
    assert cliente_admin.get("/api/v1/me").json()["papel"] == "admin"


# --- Acesso --------------------------------------------------------------------------------


def test_usuario_comum_nao_acessa(
    client: TestClient,
    usuarios: dict[str, Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, usuarios["ana"])

    listar = client.get(USUARIOS)
    resetar = reset(client, usuarios["bia"].id)

    assert listar.status_code == resetar.status_code == 403
    assert listar.json()["erro"]["codigo"] == "acesso_negado"
    assert resetar.json()["erro"]["codigo"] == "acesso_negado"


def test_usuario_comum_nao_muda_nada_ao_tentar_reset(
    client: TestClient,
    usuarios: dict[str, Usuario],
    logar: Callable[[TestClient, Usuario], str],
    novo_client: Callable[[], TestClient],
    db: Session,
) -> None:
    logar(client, usuarios["ana"])
    cliente_bia = novo_client()
    logar(cliente_bia, usuarios["bia"])

    reset(client, usuarios["bia"].id)

    assert cliente_bia.get("/api/v1/me").status_code == 200
    assert db.scalars(select(AcaoAdmin)).all() == []


def test_exige_login(client: TestClient) -> None:
    assert client.get(USUARIOS).status_code == 401
    assert reset(client, 1).status_code == 401


def test_admin_com_troca_pendente_precisa_trocar_antes(
    client: TestClient,
    admin: Usuario,
    logar: Callable[[TestClient, Usuario], str],
    db: Session,
) -> None:
    db.execute(update(Usuario).where(Usuario.id == admin.id).values(troca_senha_obrigatoria=True))
    db.commit()
    logar(client, admin)

    resposta = client.get(USUARIOS)

    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "troca_senha_obrigatoria"


# --- US2: listar e buscar ------------------------------------------------------------------


def test_lista_so_nome_email_e_criacao_em_ordem_alfabetica(
    cliente_admin: TestClient, usuarios: dict[str, Usuario]
) -> None:
    resposta = cliente_admin.get(USUARIOS)

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert [u["nome"] for u in corpo] == ["Ana Souza", "Bia Lima", "Caio Dias"]
    assert all(set(u) == {"id", "nome", "email", "criado_em"} for u in corpo)
    assert corpo[0]["id"] == usuarios["ana"].id


def test_nao_expoe_dados_pessoais_nem_o_admin(
    cliente_admin: TestClient, usuarios: dict[str, Usuario]
) -> None:
    texto = cliente_admin.get(USUARIOS).text
    for dado in ("11987654321", "Dev", "telefone", "cargo", "senha", "admin@exemplo.com"):
        assert dado not in texto


@pytest.mark.parametrize("busca", ["bi", "BIA@", "Lima", "lima"])
def test_busca_por_nome_ou_email(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], busca: str
) -> None:
    corpo = cliente_admin.get(USUARIOS, params={"busca": busca}).json()
    assert [u["email"] for u in corpo] == ["bia@exemplo.com"]


def test_busca_sem_resultado(cliente_admin: TestClient, usuarios: dict[str, Usuario]) -> None:
    assert cliente_admin.get(USUARIOS, params={"busca": "zzz"}).json() == []


def test_busca_trata_curinga_como_texto(
    cliente_admin: TestClient, usuarios: dict[str, Usuario]
) -> None:
    assert cliente_admin.get(USUARIOS, params={"busca": "%"}).json() == []


# --- US3: resetar senha --------------------------------------------------------------------


def test_reset_devolve_senha_temporaria_e_derruba_sessoes(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    novo_client: Callable[[], TestClient],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    cliente_ana = novo_client()
    logar(cliente_ana, usuarios["ana"])

    resposta = reset(cliente_admin, usuarios["ana"].id)

    assert resposta.status_code == 200
    senha = resposta.json()["senha_temporaria"]
    assert len(senha) == 12
    assert set(resposta.json()) == {"senha_temporaria"}
    assert cliente_ana.get("/api/v1/me").status_code == 401


def test_depois_do_reset_so_a_temporaria_entra_e_exige_troca(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    novo_client: Callable[[], TestClient],
) -> None:
    senha = reset(cliente_admin, usuarios["ana"].id).json()["senha_temporaria"]
    ana = novo_client()
    login = {"email": "ana@exemplo.com"}

    assert ana.post("/api/v1/auth/login", json={**login, "senha": SENHA_PADRAO}).status_code == 401
    entrou = ana.post("/api/v1/auth/login", json={**login, "senha": senha})
    assert entrou.status_code == 200
    assert entrou.json()["troca_senha_obrigatoria"] is True
    assert ana.get("/api/v1/me").status_code == 403
    troca = {"senha_atual": senha, "nova_senha": "minhaNova123"}
    assert ana.put("/api/v1/me/senha", json=troca).status_code == 204
    assert ana.get("/api/v1/me").status_code == 200


def test_reset_fica_registrado(
    cliente_admin: TestClient,
    admin: Usuario,
    usuarios: dict[str, Usuario],
    db: Session,
    relogio: RelogioFixo,
) -> None:
    relogio.avancar(hours=1)
    reset(cliente_admin, usuarios["bia"].id)

    acoes = db.scalars(select(AcaoAdmin)).all()

    assert [(a.admin_id, a.acao, a.usuario_alvo_id) for a in acoes] == [
        (admin.id, "reset_senha", usuarios["bia"].id)
    ]
    assert acoes[0].ocorrida_em == relogio.agora


def test_segundo_reset_invalida_a_primeira_temporaria(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], novo_client: Callable[[], TestClient]
) -> None:
    primeira = reset(cliente_admin, usuarios["ana"].id).json()["senha_temporaria"]
    segunda = reset(cliente_admin, usuarios["ana"].id).json()["senha_temporaria"]
    ana = novo_client()
    login = {"email": "ana@exemplo.com"}

    assert ana.post("/api/v1/auth/login", json={**login, "senha": primeira}).status_code == 401
    assert ana.post("/api/v1/auth/login", json={**login, "senha": segunda}).status_code == 200


def test_reset_de_conta_inexistente(cliente_admin: TestClient) -> None:
    resposta = reset(cliente_admin, 999_999_999)
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "nao_encontrado"


def test_reset_da_conta_do_admin_nao_e_permitido(cliente_admin: TestClient, admin: Usuario) -> None:
    assert reset(cliente_admin, admin.id).status_code == 404


def test_reset_nao_derruba_a_sessao_do_admin(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], relogio: RelogioFixo
) -> None:
    reset(cliente_admin, usuarios["ana"].id)
    relogio.avancar(seconds=1)
    assert cliente_admin.get(USUARIOS).status_code == 200


def test_rotas_de_admin_sao_so_estas(client: TestClient) -> None:
    rotas = [p for p in client.get("/openapi.json").json()["paths"] if "/admin" in p]
    assert sorted(rotas) == [USUARIOS, f"{USUARIOS}/{{usuario_id}}/reset-senha"]
