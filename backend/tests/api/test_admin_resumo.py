from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Categoria, Divida, Lancamento, Usuario
from app.services.categoria import criar_categorias_iniciais

RESUMO = "/api/v1/admin/resumo"


@pytest.fixture
def lancar(db: Session) -> Callable[..., None]:
    """Grava lançamentos direto no banco, na primeira categoria do tipo pedido."""

    def _lancar(
        usuario: Usuario, tipo: str, data: date, status: str = "realizado", valor: int = 1_000
    ) -> None:
        if not db.scalar(select(Categoria.id).where(Categoria.usuario_id == usuario.id)):
            criar_categorias_iniciais(db, usuario.id)
            db.flush()
        categoria_id = db.scalar(
            select(Categoria.id)
            .where(Categoria.usuario_id == usuario.id, Categoria.tipo == tipo)
            .order_by(Categoria.id)
        )
        db.add(
            Lancamento(
                usuario_id=usuario.id,
                categoria_id=categoria_id,
                data=data,
                valor=valor,
                tipo=tipo,
                status=status,
            )
        )
        db.flush()

    return _lancar


@pytest.fixture
def endividar(db: Session, lancar: Callable[..., None]) -> Callable[[Usuario, str], None]:
    def _endividar(usuario: Usuario, forma: str) -> None:
        lancar(usuario, "saida", date(2026, 9, 1))  # garante as categorias
        categoria_id = db.scalar(
            select(Categoria.id).where(
                Categoria.usuario_id == usuario.id, Categoria.tipo == "saida"
            )
        )
        db.add(
            Divida(
                usuario_id=usuario.id,
                categoria_id=categoria_id,
                descricao="Notebook",
                pessoa="Loja",
                direcao="devo",
                valor_total=300_000,
                parcelas=3,
                forma_pagamento=forma,
                dia_vencimento=10,
                data_inicio=date(2026, 9, 10),
            )
        )
        db.flush()

    return _endividar


def test_resumo_vazio(cliente_admin: TestClient) -> None:
    corpo = cliente_admin.get(RESUMO).json()

    assert corpo["contas"] == {"total": 0, "ativas": 0, "desativadas": 0}
    assert corpo["lancamentos"] == {"total": 0, "realizados": 0, "previstos": 0}
    assert len(corpo["por_mes"]) == 12
    assert all(m["entradas"] == m["saidas"] == 0 for m in corpo["por_mes"])
    assert [f["quantidade"] for f in corpo["dividas_por_forma"]] == [0, 0, 0, 0]


def test_conta_as_contas_sem_o_admin(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], db: Session
) -> None:
    usuarios["bia"].ativo = False
    db.commit()

    corpo = cliente_admin.get(RESUMO).json()

    assert corpo["contas"] == {"total": 3, "ativas": 2, "desativadas": 1}


def test_soma_lancamentos_de_todos_os_usuarios(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], lancar: Callable[..., None]
) -> None:
    lancar(usuarios["ana"], "entrada", date(2026, 9, 5))
    lancar(usuarios["ana"], "saida", date(2026, 9, 6), status="previsto")
    lancar(usuarios["bia"], "saida", date(2026, 8, 20))

    corpo = cliente_admin.get(RESUMO).json()

    assert corpo["lancamentos"] == {"total": 3, "realizados": 2, "previstos": 1}


def test_entradas_e_saidas_realizadas_por_mes(
    cliente_admin: TestClient, usuarios: dict[str, Usuario], lancar: Callable[..., None]
) -> None:
    lancar(usuarios["ana"], "entrada", date(2026, 9, 1))
    lancar(usuarios["bia"], "entrada", date(2026, 9, 30))
    lancar(usuarios["ana"], "saida", date(2026, 9, 15))
    lancar(usuarios["ana"], "saida", date(2026, 9, 16), status="previsto")
    lancar(usuarios["caio"], "saida", date(2025, 10, 1))
    lancar(usuarios["caio"], "saida", date(2025, 9, 30))  # fora da janela
    lancar(usuarios["caio"], "entrada", date(2026, 10, 1))  # futuro, fora da janela

    por_mes = cliente_admin.get(RESUMO).json()["por_mes"]

    assert por_mes[0] == {"mes": "2025-10", "entradas": 0, "saidas": 1}
    assert por_mes[-1] == {"mes": "2026-09", "entradas": 2, "saidas": 1}
    assert por_mes[-2] == {"mes": "2026-08", "entradas": 0, "saidas": 0}


def test_dividas_por_forma_de_pagamento(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    endividar: Callable[[Usuario, str], None],
) -> None:
    endividar(usuarios["ana"], "cartao")
    endividar(usuarios["bia"], "pix")
    endividar(usuarios["caio"], "pix")

    formas = cliente_admin.get(RESUMO).json()["dividas_por_forma"]

    assert formas == [
        {"forma": "pix", "quantidade": 2},
        {"forma": "cartao", "quantidade": 1},
        {"forma": "boleto", "quantidade": 0},
        {"forma": "dinheiro", "quantidade": 0},
    ]


def test_resumo_nao_traz_valores_nem_usuarios(
    cliente_admin: TestClient,
    usuarios: dict[str, Usuario],
    lancar: Callable[..., None],
    endividar: Callable[[Usuario, str], None],
) -> None:
    lancar(usuarios["ana"], "entrada", date(2026, 9, 5), valor=123_456)
    endividar(usuarios["bia"], "boleto")

    resposta = cliente_admin.get(RESUMO)

    assert set(resposta.json()) == {"contas", "lancamentos", "por_mes", "dividas_por_forma"}
    for proibido in ("123456", "300000", "valor", "usuario", "email", "ana@", "Ana"):
        assert proibido not in resposta.text


def test_usuario_comum_nao_ve_o_resumo(
    client: TestClient,
    usuarios: dict[str, Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, usuarios["ana"])

    resposta = client.get(RESUMO)

    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "acesso_negado"


def test_resumo_exige_login(client: TestClient) -> None:
    assert client.get(RESUMO).status_code == 401
