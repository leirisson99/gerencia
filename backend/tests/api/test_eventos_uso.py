"""US2 da spec 018: cada ação bem-sucedida grava um evento de uso, sem conteúdo."""

from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import EventoUso, Usuario
from app.services.evento_uso import limpar_antigos
from tests.conftest import SENHA_PADRAO, Conta, RelogioFixo

LANCAMENTOS = "/api/v1/lancamentos"


@pytest.fixture(autouse=True)
def hoje_15_de_outubro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 10, 15, 15, 0, tzinfo=UTC)


def eventos(db: Session, usuario: Usuario) -> list[str]:
    db.expire_all()
    return list(
        db.scalars(
            select(EventoUso.tipo).where(EventoUso.usuario_id == usuario.id).order_by(EventoUso.id)
        )
    )


def ok(resposta: Any, status: int = 200) -> dict[str, Any]:
    assert resposta.status_code == status, resposta.text
    return resposta.json() if resposta.content else {}


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta], db: Session) -> Conta:
    """Ana `clt_prestador`, com o salário que abre o ciclo já lançado (e fora da contagem)."""
    conta = criar_conta(client)
    conta.usuario.tipo_renda = "clt_prestador"
    db.commit()
    ok(
        client.post(
            LANCAMENTOS,
            json={
                "valor": 500_000,
                "categoria_id": conta.categorias["Salário"],
                "data": "2026-10-05",
            },
        ),
        201,
    )
    db.execute(EventoUso.__table__.delete())
    return conta


def lancar(client: TestClient, conta: Conta, **extra: Any) -> Any:
    corpo = {"valor": 1_000, "categoria_id": conta.categorias["Alimentação"], "data": "2026-10-10"}
    return client.post(LANCAMENTOS, json={**corpo, **extra})


# --- conta e acesso --------------------------------------------------------------------------


def test_cadastro_grava_conta_criada(client: TestClient, db: Session) -> None:
    corpo = ok(
        client.post(
            "/api/v1/auth/cadastro",
            json={
                "nome": "Ana Souza",
                "email": "ana@exemplo.com",
                "telefone": "(11) 98765-4321",
                "cargo": "Dev",
                "senha": SENHA_PADRAO,
            },
        ),
        201,
    )

    assert eventos(db, db.get(Usuario, corpo["id"])) == ["conta_criada"]


def test_login_grava_e_falhas_nao(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    db: Session,
) -> None:
    ana = criar_usuario()
    bia = criar_usuario(email="bia@exemplo.com", ativo=False)
    login = "/api/v1/auth/login"

    assert client.post(login, json={"email": ana.email, "senha": "errada"}).status_code == 401
    assert client.post(login, json={"email": bia.email, "senha": SENHA_PADRAO}).status_code == 403
    ok(client.post(login, json={"email": ana.email, "senha": SENHA_PADRAO}))

    assert eventos(db, ana) == ["login"]
    assert eventos(db, bia) == []


def test_login_do_admin_nao_grava(client: TestClient, admin: Usuario, db: Session) -> None:
    ok(
        client.post(
            "/api/v1/auth/login", json={"email": "admin@exemplo.com", "senha": "segredoAdmin1"}
        )
    )

    assert eventos(db, admin) == []


def test_senha_e_perfil(client: TestClient, conta: Conta, db: Session) -> None:
    assert (
        client.put(
            "/api/v1/me/senha", json={"senha_atual": "errada", "nova_senha": "novaSenha456"}
        ).status_code
        == 400
    )
    ok(
        client.put(
            "/api/v1/me/senha", json={"senha_atual": SENHA_PADRAO, "nova_senha": "novaSenha456"}
        ),
        204,
    )
    ok(client.patch("/api/v1/me", json={"cargo": "Tech lead"}))

    assert eventos(db, conta.usuario) == ["senha_trocada", "perfil_atualizado"]


# --- lançamentos e importação ----------------------------------------------------------------


def test_criar_editar_excluir_lancamento(client: TestClient, conta: Conta, db: Session) -> None:
    lancamento = ok(lancar(client, conta), 201)
    ok(client.patch(f"{LANCAMENTOS}/{lancamento['id']}", json={"valor": 2_000}))
    ok(client.delete(f"{LANCAMENTOS}/{lancamento['id']}"), 204)

    assert eventos(db, conta.usuario) == [
        "lancamento_criado",
        "lancamento_editado",
        "lancamento_excluido",
    ]


def test_lancamento_recusado_nao_grava(client: TestClient, conta: Conta, db: Session) -> None:
    assert lancar(client, conta, data="2026-09-01").status_code == 409  # antes do salário
    assert lancar(client, conta, valor=0).status_code == 422

    assert eventos(db, conta.usuario) == []


def test_salario_com_recorrencia_grava_um_evento(
    client: TestClient, conta: Conta, db: Session, relogio: RelogioFixo
) -> None:
    ok(
        client.post(
            "/api/v1/recorrencias",
            json={
                "descricao": "Aluguel",
                "valor": 150_000,
                "categoria_id": conta.categorias["Moradia"],
                "dia": 10,
            },
        ),
        201,
    )
    relogio.agora = datetime(2026, 11, 5, 15, 0, tzinfo=UTC)
    ok(
        lancar(
            client,
            conta,
            valor=500_000,
            categoria_id=conta.categorias["Salário"],
            data="2026-11-05",
        ),
        201,
    )

    assert eventos(db, conta.usuario) == ["recorrencia_criada", "lancamento_criado"]


def test_importacao_grava_um_evento(client: TestClient, conta: Conta, db: Session) -> None:
    linhas = [
        {
            "id_externo": f"ext-{n}",
            "data": "2026-10-1" + str(n),
            "valor": 1_000 + n,
            "tipo": "saida",
            "descricao": f"Mercado {n}",
            "categoria_id": conta.categorias["Alimentação"],
        }
        for n in range(3)
    ]
    ok(client.post("/api/v1/importacoes", json={"linhas": linhas}), 201)

    assert eventos(db, conta.usuario) == ["extrato_importado"]


# --- categorias, recorrências e dívidas ------------------------------------------------------


def test_categoria_e_recorrencia(client: TestClient, conta: Conta, db: Session) -> None:
    categoria = ok(client.post("/api/v1/categorias", json={"nome": "Pets", "tipo": "saida"}), 201)
    ok(client.patch(f"/api/v1/categorias/{categoria['id']}", json={"nome": "Bichos"}))
    recorrencia = ok(
        client.post(
            "/api/v1/recorrencias",
            json={
                "descricao": "Internet",
                "valor": 10_000,
                "categoria_id": categoria["id"],
                "dia": 20,
            },
        ),
        201,
    )
    ok(client.patch(f"/api/v1/recorrencias/{recorrencia['id']}", json={"dia": 21}))

    assert eventos(db, conta.usuario) == [
        "categoria_criada",
        "categoria_editada",
        "recorrencia_criada",
        "recorrencia_editada",
    ]


def test_divida_com_parcelas_grava_um_evento(client: TestClient, conta: Conta, db: Session) -> None:
    ok(
        client.post(
            "/api/v1/dividas",
            json={
                "descricao": "Notebook",
                "pessoa": "Loja X",
                "direcao": "devo",
                "valor_total": 100_000,
                "parcelas": 3,
                "forma_pagamento": "pix",
                "dia_vencimento": 15,
                "data_inicio": "2026-10-05",
                "categoria_id": conta.categorias["Outros"],
            },
        ),
        201,
    )

    assert eventos(db, conta.usuario) == ["divida_criada"]


# --- cartelas e serviços ---------------------------------------------------------------------


def test_cartela(client: TestClient, conta: Conta, db: Session) -> None:
    cartela = ok(client.post("/api/v1/cartelas", json={"nome": "Viagem", "meta": 100_000}), 201)
    casa = cartela["casas"][0]
    caminho = f"/api/v1/cartelas/{cartela['id']}/casas/{casa['id']}/deposito"
    ok(client.post(caminho))
    assert client.post(caminho).status_code == 409  # já depositada
    ok(client.delete(caminho))

    assert eventos(db, conta.usuario) == ["cartela_criada", "deposito_feito", "deposito_desfeito"]


def test_servico(client: TestClient, conta: Conta, db: Session) -> None:
    servico = ok(
        client.post(
            "/api/v1/servicos",
            json={
                "cliente": "Loja da Maria",
                "valor": 80_000,
                "data_prevista": "2026-10-20",
                "categoria_id": conta.categorias["Renda extra"],
            },
        ),
        201,
    )
    url = f"/api/v1/servicos/{servico['id']}"
    ok(client.patch(url, json={"valor": 90_000}))
    ok(client.post(f"{url}/recebimento", json={"data": "2026-10-15"}))
    ok(client.delete(f"{url}/recebimento"))
    ok(client.delete(url), 204)

    assert eventos(db, conta.usuario) == [
        "servico_criado",
        "servico_editado",
        "servico_recebido",
        "recebimento_desfeito",
        "servico_excluido",
    ]


# --- lembretes e push ------------------------------------------------------------------------


def test_lembretes(client: TestClient, conta: Conta, db: Session) -> None:
    livres = "/api/v1/lembretes/livres"
    lembrete = ok(client.post(livres, json={"texto": "Ligar", "data": "2026-10-16"}), 201)
    url = f"{livres}/{lembrete['id']}"
    ok(client.patch(url, json={"texto": "Ligar para o banco"}))
    ok(client.patch(url, json={"concluido": True, "texto": "Liguei"}))
    ok(client.patch(url, json={"concluido": False}))
    ok(client.delete(url), 204)

    assert eventos(db, conta.usuario) == [
        "lembrete_criado",
        "lembrete_editado",
        "lembrete_concluido",
        "lembrete_editado",
        "lembrete_excluido",
    ]


def test_push(client: TestClient, conta: Conta, db: Session, settings_teste: Settings) -> None:
    settings_teste.vapid_chave_publica = "BPublicaDeTeste"
    settings_teste.vapid_chave_privada = "privada-de-teste"
    settings_teste.vapid_contato = "mailto:admin@exemplo.com"
    endpoint = "https://fcm.googleapis.com/fcm/send/abc123"
    inscricao = {"endpoint": endpoint, "keys": {"p256dh": "p" * 87, "auth": "a" * 22}}

    ok(client.put("/api/v1/push/inscricao", json=inscricao), 204)
    ok(client.request("DELETE", "/api/v1/push/inscricao", json={"endpoint": endpoint}), 204)
    assert (
        client.request("DELETE", "/api/v1/push/inscricao", json={"endpoint": endpoint}).status_code
        == 404
    )

    assert eventos(db, conta.usuario) == ["push_ativado", "push_removido"]


# --- isolamento e forma da tabela ------------------------------------------------------------


def test_eventos_sao_de_quem_agiu(
    client: TestClient,
    conta: Conta,
    criar_usuario: Callable[..., Usuario],
    db: Session,
) -> None:
    bia = criar_usuario(email="bia@exemplo.com")
    ok(lancar(client, conta), 201)

    assert eventos(db, conta.usuario) == ["lancamento_criado"]
    assert eventos(db, bia) == []


def test_tabela_nao_guarda_conteudo() -> None:
    assert set(EventoUso.__table__.columns.keys()) == {"id", "usuario_id", "tipo", "ocorrido_em"}


# --- retenção --------------------------------------------------------------------------------


def test_limpar_antigos_apaga_so_os_de_mais_de_12_meses(
    criar_usuario: Callable[..., Usuario], db: Session, relogio: RelogioFixo
) -> None:
    ana = criar_usuario()
    agora = relogio.agora
    for dias, tipo in ((366, "login"), (330, "lancamento_criado"), (0, "perfil_atualizado")):
        db.add(EventoUso(usuario_id=ana.id, tipo=tipo, ocorrido_em=agora - timedelta(days=dias)))
    db.commit()

    assert limpar_antigos(db, agora) == 1
    assert eventos(db, ana) == ["lancamento_criado", "perfil_atualizado"]
