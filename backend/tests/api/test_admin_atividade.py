"""Spec 018: detalhe da conta, linha do tempo e auditoria da visita do administrador."""

import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import AcaoAdmin, EventoUso, Usuario
from tests.api.conftest import USUARIOS
from tests.conftest import Conta, RelogioFixo


@pytest.fixture(autouse=True)
def hoje_15_de_outubro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 10, 15, 15, 0, tzinfo=UTC)


def ok(resposta: Any, status: int = 200) -> Any:
    assert resposta.status_code == status, resposta.text
    return resposta.json()


@pytest.fixture
def cliente_ana(novo_client: Callable[[], TestClient]) -> TestClient:
    return novo_client()


@pytest.fixture
def ana(cliente_ana: TestClient, criar_conta: Callable[..., Conta], db: Session) -> Conta:
    """Ana `clt_prestador`, logada no próprio navegador, com o salário de 05/10 lançado."""
    conta = criar_conta(cliente_ana, "ana@exemplo.com")
    conta.usuario.tipo_renda = "clt_prestador"
    conta.usuario.telefone = "11999990000"
    conta.usuario.cargo = "SEGREDO-CARGO"
    db.commit()
    ok(
        cliente_ana.post(
            "/api/v1/lancamentos",
            json={
                "valor": 500_000,
                "categoria_id": conta.categorias["Salário"],
                "data": "2026-10-05",
            },
        ),
        201,
    )
    return conta


def usar_tudo(c: TestClient, conta: Conta) -> None:
    """Uso típico, com textos e valores marcados para o teste de privacidade."""
    cat = conta.categorias
    nova = ok(c.post("/api/v1/categorias", json={"nome": "SEGREDO-CAT", "tipo": "saida"}), 201)
    for _ in range(2):
        ok(
            c.post(
                "/api/v1/lancamentos",
                json={
                    "valor": 123_457,
                    "categoria_id": nova["id"],
                    "data": "2026-10-10",
                    "descricao": "SEGREDO-DESC",
                },
            ),
            201,
        )
    linhas = [
        {
            "id_externo": f"ext-{n}",
            "data": "2026-10-12",
            "valor": 2_000 + n,
            "tipo": "saida",
            "descricao": "SEGREDO-EXTRATO",
            "categoria_id": cat["Alimentação"],
        }
        for n in range(2)
    ]
    ok(c.post("/api/v1/importacoes", json={"linhas": linhas}), 201)
    ok(
        c.post(
            "/api/v1/recorrencias",
            json={
                "descricao": "SEGREDO-REC",
                "valor": 9_000,
                "categoria_id": cat["Moradia"],
                "dia": 20,
            },
        ),
        201,
    )
    ok(
        c.post(
            "/api/v1/dividas",
            json={
                "descricao": "SEGREDO-DIV",
                "pessoa": "SEGREDO-PESSOA",
                "direcao": "devo",
                "valor_total": 30_000,
                "parcelas": 3,
                "forma_pagamento": "pix",
                "dia_vencimento": 20,
                "data_inicio": "2026-10-05",
                "categoria_id": cat["Outros"],
            },
        ),
        201,
    )
    cartela = ok(c.post("/api/v1/cartelas", json={"nome": "SEGREDO-CART", "meta": 10_000}), 201)
    casa = cartela["casas"][0]
    ok(c.post(f"/api/v1/cartelas/{cartela['id']}/casas/{casa['id']}/deposito"))
    ok(
        c.post(
            "/api/v1/servicos",
            json={
                "cliente": "SEGREDO-CLI",
                "valor": 80_000,
                "data_prevista": "2026-10-20",
                "categoria_id": cat["Renda extra"],
            },
        ),
        201,
    )
    ok(
        c.post("/api/v1/lembretes/livres", json={"texto": "SEGREDO-LEMB", "data": "2026-10-16"}),
        201,
    )


def detalhe(cliente: TestClient, usuario_id: int) -> dict[str, Any]:
    return ok(cliente.get(f"{USUARIOS}/{usuario_id}"))


def visitas(db: Session, usuario: Usuario) -> int:
    return db.scalar(
        select(func.count()).where(
            AcaoAdmin.usuario_alvo_id == usuario.id, AcaoAdmin.acao == "ver_atividade"
        )
    )


# --- US1: detalhe ----------------------------------------------------------------------------


def test_detalhe_traz_contagens_por_funcionalidade(
    cliente_admin: TestClient, cliente_ana: TestClient, ana: Conta
) -> None:
    usar_tudo(cliente_ana, ana)

    corpo = detalhe(cliente_admin, ana.usuario.id)

    assert corpo["conta"] == {
        "id": ana.usuario.id,
        "nome": "Ana Souza",
        "email": "ana@exemplo.com",
        "criado_em": corpo["conta"]["criado_em"],
        "ativo": True,
    }
    assert corpo["sessoes_abertas"] == 1
    assert corpo["contagens"] == {
        "lancamentos_manuais": 3,  # salário + 2 gastos
        "lancamentos_importados": 2,
        "lancamentos_gerados": 6,  # 3 parcelas, 1 recorrência, 1 depósito, 1 serviço
        "importacoes": 1,
        "recorrencias": 1,
        "dividas": 1,
        "cartelas": 1,
        "depositos": 1,
        "servicos": 1,
        "lembretes": 1,
        "aparelhos_push": 0,
        "retiradas": 0,
    }


def test_conta_sem_uso_vem_com_zeros(
    cliente_admin: TestClient, criar_usuario: Callable[..., Usuario]
) -> None:
    bia = criar_usuario(email="bia@exemplo.com")

    corpo = detalhe(cliente_admin, bia.id)

    assert corpo["ultimo_acesso_em"] is None
    assert corpo["sessoes_abertas"] == 0
    assert set(corpo["contagens"].values()) == {0}
    assert corpo["acoes_admin"] == [
        {"acao": "ver_atividade", "ocorrida_em": "2026-10-15T15:00:00Z", "admin_nome": "Admin"}
    ]


def test_sessoes_abertas_ignoram_as_vencidas(
    cliente_admin: TestClient,
    ana: Conta,
    novo_client: Callable[[], TestClient],
    logar: Callable[[TestClient, Usuario], str],
    relogio: RelogioFixo,
) -> None:
    relogio.agora -= timedelta(days=31)
    logar(novo_client(), ana.usuario)  # vencida por inatividade
    relogio.agora += timedelta(days=31)
    logar(novo_client(), ana.usuario)

    corpo = detalhe(cliente_admin, ana.usuario.id)

    assert corpo["sessoes_abertas"] == 2  # a da fixture e a de agora
    assert corpo["ultimo_acesso_em"] is not None


def test_conta_desativada_abre_sem_sessoes(cliente_admin: TestClient, ana: Conta) -> None:
    ok(cliente_admin.post(f"{USUARIOS}/{ana.usuario.id}/desativar"))

    corpo = detalhe(cliente_admin, ana.usuario.id)

    assert corpo["conta"]["ativo"] is False
    assert corpo["sessoes_abertas"] == 0


def test_detalhe_nao_traz_conteudo(
    cliente_admin: TestClient, cliente_ana: TestClient, ana: Conta
) -> None:
    usar_tudo(cliente_ana, ana)

    texto = json.dumps(detalhe(cliente_admin, ana.usuario.id)) + json.dumps(
        ok(cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}/eventos"))
    )

    assert "SEGREDO" not in texto
    assert "123457" not in texto
    assert "11999990000" not in texto
    assert "telefone" not in texto and "cargo" not in texto


@pytest.mark.parametrize("sufixo", ["", "/eventos"])
def test_acesso(
    sufixo: str,
    cliente_admin: TestClient,
    admin: Usuario,
    cliente_ana: TestClient,
    ana: Conta,
    novo_client: Callable[[], TestClient],
) -> None:
    assert cliente_admin.get(f"{USUARIOS}/999999{sufixo}").status_code == 404
    assert cliente_admin.get(f"{USUARIOS}/{admin.id}{sufixo}").status_code == 404

    proprio = cliente_ana.get(f"{USUARIOS}/{ana.usuario.id}{sufixo}")
    assert proprio.status_code == 403
    assert proprio.json()["erro"]["codigo"] == "acesso_negado"

    assert novo_client().get(f"{USUARIOS}/{ana.usuario.id}{sufixo}").status_code == 401


# --- US2: linha do tempo ---------------------------------------------------------------------


def test_linha_do_tempo_mostra_so_tipo_e_hora(
    cliente_admin: TestClient, cliente_ana: TestClient, ana: Conta
) -> None:
    lancamento = ok(
        cliente_ana.post(
            "/api/v1/lancamentos",
            json={"valor": 1_000, "categoria_id": ana.categorias["Lazer"], "data": "2026-10-10"},
        ),
        201,
    )
    ok(cliente_ana.patch(f"/api/v1/lancamentos/{lancamento['id']}", json={"valor": 2_000}))

    corpo = ok(cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}/eventos"))

    assert [item["tipo"] for item in corpo["itens"]] == [
        "lancamento_editado",
        "lancamento_criado",
        "lancamento_criado",  # o salário da fixture
    ]
    assert set(corpo["itens"][0]) == {"tipo", "ocorrido_em"}
    assert corpo["proximo"] is None


def test_paginacao_sem_repetir_nem_pular(
    cliente_admin: TestClient, ana: Conta, criar_usuario: Callable[..., Usuario], db: Session
) -> None:
    bia = criar_usuario(email="bia@exemplo.com")
    db.execute(EventoUso.__table__.delete())
    db.add_all(EventoUso(usuario_id=ana.usuario.id, tipo="login") for _ in range(120))
    db.add_all(EventoUso(usuario_id=bia.id, tipo="login") for _ in range(5))
    db.commit()
    ids_ana = set(db.scalars(select(EventoUso.id).where(EventoUso.usuario_id == ana.usuario.id)))
    url = f"{USUARIOS}/{ana.usuario.id}/eventos"

    paginas = [ok(cliente_admin.get(url))]
    # Um evento novo no meio da leitura não desloca as páginas seguintes.
    db.add(EventoUso(usuario_id=ana.usuario.id, tipo="lancamento_criado"))
    db.commit()
    while paginas[-1]["proximo"] is not None:
        paginas.append(ok(cliente_admin.get(url, params={"antes": paginas[-1]["proximo"]})))

    assert [len(p["itens"]) for p in paginas] == [50, 50, 20]
    vistos = [p["proximo"] for p in paginas[:-1]]
    assert vistos == sorted(vistos, reverse=True)
    assert sum(len(p["itens"]) for p in paginas) == len(ids_ana)


@pytest.mark.parametrize("antes", ["0", "-1", "abc"])
def test_cursor_invalido(cliente_admin: TestClient, ana: Conta, antes: str) -> None:
    resposta = cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}/eventos", params={"antes": antes})

    assert resposta.status_code == 422


# --- US3: ações do administrador e auditoria da visita ---------------------------------------


def test_visita_registrada_uma_vez_a_cada_30_minutos(
    cliente_admin: TestClient, ana: Conta, relogio: RelogioFixo, db: Session
) -> None:
    detalhe(cliente_admin, ana.usuario.id)
    ok(cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}/eventos"))
    relogio.avancar(minutes=29)
    detalhe(cliente_admin, ana.usuario.id)
    assert visitas(db, ana.usuario) == 1

    relogio.avancar(minutes=1)
    ok(cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}/eventos"))
    assert visitas(db, ana.usuario) == 2


def test_so_eventos_tambem_e_auditado(cliente_admin: TestClient, ana: Conta, db: Session) -> None:
    ok(cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}/eventos"))

    assert visitas(db, ana.usuario) == 1


def test_acoes_admin_da_conta(
    cliente_admin: TestClient,
    ana: Conta,
    criar_usuario: Callable[..., Usuario],
    relogio: RelogioFixo,
) -> None:
    bia = criar_usuario(email="bia@exemplo.com")
    ok(cliente_admin.post(f"{USUARIOS}/{bia.id}/desativar"))
    for acao in ("reset-senha", "desativar", "reativar"):
        relogio.avancar(minutes=1)
        ok(cliente_admin.post(f"{USUARIOS}/{ana.usuario.id}/{acao}"))
    relogio.avancar(minutes=1)

    acoes = detalhe(cliente_admin, ana.usuario.id)["acoes_admin"]

    assert [a["acao"] for a in acoes] == [
        "ver_atividade",
        "reativar_conta",
        "desativar_conta",
        "reset_senha",
    ]
    assert {a["admin_nome"] for a in acoes} == {"Admin"}


def test_retiradas_contam_no_detalhe(
    cliente_admin: TestClient, cliente_ana: TestClient, ana: Conta, db: Session
) -> None:
    """Spec 019: retiradas entram nas contagens; os dois lados contam como gerados."""
    ok(cliente_ana.patch("/api/v1/me", json={"tem_pj": True}))
    ok(cliente_ana.post("/api/v1/retiradas", json={"valor": 10_000, "data": "2026-10-10"}), 201)

    contagens = detalhe(cliente_admin, ana.usuario.id)["contagens"]

    assert contagens["retiradas"] == 1
    assert contagens["lancamentos_gerados"] == 2
    assert contagens["lancamentos_manuais"] == 1  # o salário da fixture
