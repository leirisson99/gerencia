"""US2 da spec 019: retirada da PJ para a PF, sempre com os dois lados juntos."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Categoria, EventoUso, Lancamento, Retirada
from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/retiradas"
LANCAMENTOS = "/api/v1/lancamentos"


@pytest.fixture(autouse=True)
def hoje_31_de_outubro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 10, 31, 15, 0, tzinfo=UTC)


def ok(resposta: Any, status: int = 200) -> Any:
    assert resposta.status_code == status, resposta.text
    return resposta.json() if resposta.content else None


def erro(resposta: Any, status: int) -> dict[str, Any]:
    assert resposta.status_code == status, resposta.text
    return resposta.json()["erro"]


@pytest.fixture
def com_tipo(
    client: TestClient, criar_conta: Callable[..., Conta], db: Session
) -> Callable[..., Conta]:
    def _criar(tipo: str = "prestador", tem_pj: bool = True, email: str = "carlos@exemplo.com"):
        conta = criar_conta(client, email)
        conta.usuario.tipo_renda = tipo
        db.commit()
        if tem_pj:
            ok(client.patch("/api/v1/me", json={"tem_pj": True}))
        conta.categorias = {
            c.nome: c.id
            for c in db.scalars(select(Categoria).where(Categoria.usuario_id == conta.usuario.id))
        }
        return conta

    return _criar


@pytest.fixture
def carlos(com_tipo: Callable[..., Conta]) -> Conta:
    return com_tipo()


def lancar(client: TestClient, conta: Conta, categoria: str, valor: int, data: str, **extra: Any):
    corpo = {"valor": valor, "categoria_id": conta.categorias[categoria], "data": data}
    return ok(client.post(LANCAMENTOS, json={**corpo, **extra}), 201)


def retirar(client: TestClient, valor: int = 500_000, data: str = "2026-10-25", **extra: Any):
    return client.post(URL, json={"valor": valor, "data": data, **extra})


def saldo(client: TestClient, carteira: str) -> int:
    return ok(client.get("/api/v1/ciclos/2026-10-01/resumo", params={"carteira": carteira}))[
        "saldo"
    ]


def lados(db: Session, retirada: dict[str, Any]) -> tuple[Lancamento, Lancamento]:
    db.expire_all()
    return db.get(Lancamento, retirada["lancamento_pj_id"]), db.get(
        Lancamento, retirada["lancamento_pf_id"]
    )


# --- criar -----------------------------------------------------------------------------------


def test_cria_os_dois_lados(client: TestClient, carlos: Conta, db: Session) -> None:
    retirada = ok(retirar(client, descricao="Pró-labore de outubro"), 201)

    pj, pf = lados(db, retirada)
    assert (pj.carteira, pj.tipo, pj.categoria_id) == (
        "pj",
        "saida",
        carlos.categorias["Retirada para PF"],
    )
    assert (pf.carteira, pf.tipo, pf.categoria_id) == (
        "pf",
        "entrada",
        carlos.categorias["Pró-labore e lucros"],
    )
    for lado in (pj, pf):
        assert (lado.valor, lado.data.isoformat(), lado.status, lado.conta_no_saldo) == (
            500_000,
            "2026-10-25",
            "realizado",
            True,
        )
        assert lado.descricao == "Pró-labore de outubro"


def test_exemplo_do_carlos(client: TestClient, carlos: Conta) -> None:
    """SC-001: PJ fecha outubro com R$ 2.625,00 e a PF com R$ 2.300,00."""
    lancar(client, carlos, "Renda extra", 800_000, "2026-10-05", carteira="pj")
    lancar(client, carlos, "Outros", 7_500, "2026-10-20", carteira="pj")
    lancar(client, carlos, "Outros", 30_000, "2026-10-20", carteira="pj")
    ok(retirar(client), 201)
    lancar(client, carlos, "Moradia", 180_000, "2026-10-26")
    lancar(client, carlos, "Alimentação", 90_000, "2026-10-28")

    assert saldo(client, "pj") == 262_500
    assert saldo(client, "pf") == 230_000


# --- editar e excluir ------------------------------------------------------------------------


def test_editar_muda_os_dois_lados(client: TestClient, carlos: Conta, db: Session) -> None:
    retirada = ok(retirar(client), 201)

    editada = ok(
        client.patch(
            f"{URL}/{retirada['id']}",
            json={"valor": 450_000, "data": "2026-10-24", "descricao": "Lucros"},
        )
    )

    assert (editada["valor"], editada["data"], editada["descricao"]) == (
        450_000,
        "2026-10-24",
        "Lucros",
    )
    for lado in lados(db, retirada):
        assert (lado.valor, lado.data.isoformat(), lado.descricao) == (
            450_000,
            "2026-10-24",
            "Lucros",
        )


def test_excluir_remove_os_dois_lados(client: TestClient, carlos: Conta, db: Session) -> None:
    retirada = ok(retirar(client), 201)

    ok(client.delete(f"{URL}/{retirada['id']}"), 204)

    db.expire_all()
    assert db.get(Retirada, retirada["id"]) is None
    assert lados(db, retirada) == (None, None)


def test_lados_presos_a_retirada(client: TestClient, carlos: Conta) -> None:
    retirada = ok(retirar(client), 201)

    for lado in (retirada["lancamento_pj_id"], retirada["lancamento_pf_id"]):
        for resposta in (
            client.patch(f"{LANCAMENTOS}/{lado}", json={"valor": 1}),
            client.patch(f"{LANCAMENTOS}/{lado}", json={"carteira": "pf"}),
            client.delete(f"{LANCAMENTOS}/{lado}"),
        ):
            assert erro(resposta, 409)["codigo"] == "lancamento_de_retirada"


# --- validações ------------------------------------------------------------------------------


def test_valor_e_data_invalidos(client: TestClient, carlos: Conta, db: Session) -> None:
    assert "valor" in erro(retirar(client, valor=0), 422)["campos"]
    assert "data" in erro(retirar(client, data="2026-11-01"), 422)["campos"]
    retirada = ok(retirar(client), 201)
    assert (
        "valor" in erro(client.patch(f"{URL}/{retirada['id']}", json={"valor": 0}), 422)["campos"]
    )
    assert db.scalar(select(func.count()).select_from(Retirada)) == 1


def test_exige_a_pj(client: TestClient, com_tipo: Callable[..., Conta]) -> None:
    com_tipo(tem_pj=False)

    assert erro(retirar(client), 409)["codigo"] == "carteira_pj_desligada"
    assert erro(client.get(URL), 409)["codigo"] == "carteira_pj_desligada"


def test_lado_pf_respeita_o_ciclo_do_salario(
    client: TestClient, com_tipo: Callable[..., Conta], db: Session
) -> None:
    ana = com_tipo("clt_prestador")

    assert erro(retirar(client), 409)["codigo"] == "salario_necessario"
    lancar(client, ana, "Salário", 500_000, "2026-10-05")
    assert erro(retirar(client, data="2026-10-01"), 409)["codigo"] == "antes_do_primeiro_ciclo"
    assert db.scalar(select(func.count()).select_from(Retirada)) == 0
    ok(retirar(client, data="2026-10-06"), 201)


# --- leitura e isolamento --------------------------------------------------------------------


def test_lista_e_obtem(client: TestClient, carlos: Conta) -> None:
    antiga = ok(retirar(client, data="2026-10-10"), 201)
    nova = ok(retirar(client, data="2026-10-25"), 201)

    assert [r["id"] for r in ok(client.get(URL))] == [nova["id"], antiga["id"]]
    assert ok(client.get(f"{URL}/{antiga['id']}")) == antiga


def test_retirada_de_outro_usuario(
    client: TestClient,
    carlos: Conta,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    db: Session,
) -> None:
    retirada = ok(retirar(client), 201)
    bia_cliente = novo_client()
    bia = criar_conta(bia_cliente, "bia@exemplo.com")
    bia.usuario.tipo_renda = "prestador"
    db.commit()
    ok(bia_cliente.patch("/api/v1/me", json={"tem_pj": True}))

    assert ok(bia_cliente.get(URL)) == []
    for resposta in (
        bia_cliente.get(f"{URL}/{retirada['id']}"),
        bia_cliente.patch(f"{URL}/{retirada['id']}", json={"valor": 1}),
        bia_cliente.delete(f"{URL}/{retirada['id']}"),
    ):
        assert resposta.status_code == 404


def test_eventos_de_uso(client: TestClient, carlos: Conta, db: Session) -> None:
    db.execute(EventoUso.__table__.delete())
    retirada = ok(retirar(client), 201)
    ok(client.patch(f"{URL}/{retirada['id']}", json={"valor": 1_000}))
    ok(client.delete(f"{URL}/{retirada['id']}"), 204)

    db.expire_all()
    tipos = list(db.scalars(select(EventoUso.tipo).order_by(EventoUso.id)))
    assert tipos == ["retirada_feita", "retirada_editada", "retirada_excluida"]


def test_desligar_pj_com_retirada(client: TestClient, carlos: Conta) -> None:
    ok(retirar(client), 201)

    assert erro(client.patch("/api/v1/me", json={"tem_pj": False}), 409)["codigo"] == (
        "pj_com_dados"
    )
