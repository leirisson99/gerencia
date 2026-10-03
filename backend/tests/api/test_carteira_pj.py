"""Spec 019: carteiras PF e PJ — perfil, ciclo e saldo por carteira, recorrências e troca."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Categoria, Lancamento
from tests.conftest import Conta, RelogioFixo

ME = "/api/v1/me"
LANCAMENTOS = "/api/v1/lancamentos"
RECORRENCIAS = "/api/v1/recorrencias"


@pytest.fixture(autouse=True)
def hoje_15_de_outubro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 10, 15, 15, 0, tzinfo=UTC)


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
    def _criar(tipo: str, tem_pj: bool = False) -> Conta:
        conta = criar_conta(client)
        conta.usuario.tipo_renda = tipo
        db.commit()
        if tem_pj:
            ok(client.patch(ME, json={"tem_pj": True}))
            conta.categorias = {
                c.nome: c.id
                for c in db.scalars(
                    select(Categoria).where(Categoria.usuario_id == conta.usuario.id)
                )
            }
        return conta

    return _criar


@pytest.fixture
def carlos(com_tipo: Callable[..., Conta]) -> Conta:
    """Designer MEI: `prestador` com a PJ ligada."""
    return com_tipo("prestador", tem_pj=True)


def lancar(client: TestClient, conta: Conta, categoria: str, valor: int, **extra: Any) -> Any:
    corpo = {"valor": valor, "categoria_id": conta.categorias[categoria], "data": "2026-10-10"}
    return client.post(LANCAMENTOS, json={**corpo, **extra})


def resumo(client: TestClient, carteira: str | None = None) -> dict[str, Any]:
    params = {"carteira": carteira} if carteira else {}
    return ok(client.get("/api/v1/ciclos/2026-10-01/resumo", params=params))


# --- US1: ligar a PJ -------------------------------------------------------------------------


@pytest.mark.parametrize("tipo", ["prestador", "clt_prestador"])
def test_quem_presta_servico_liga_a_pj(
    client: TestClient, com_tipo: Callable[..., Conta], tipo: str
) -> None:
    com_tipo(tipo)

    assert ok(client.patch(ME, json={"tem_pj": True}))["tem_pj"] is True
    assert ok(client.get(ME))["tem_pj"] is True


def test_clt_nao_liga_a_pj(client: TestClient, com_tipo: Callable[..., Conta]) -> None:
    com_tipo("clt")

    assert erro(client.patch(ME, json={"tem_pj": True}), 409)["codigo"] == "tipo_sem_pj"
    assert ok(client.get(ME))["tem_pj"] is False


def test_ligar_cria_as_categorias_de_sistema_uma_vez(
    client: TestClient, com_tipo: Callable[..., Conta]
) -> None:
    com_tipo("prestador")
    ok(client.patch(ME, json={"tem_pj": True}))
    ok(client.patch(ME, json={"tem_pj": True}))

    categorias = ok(client.get("/api/v1/categorias"))
    da_pj = {(c["nome"], c["tipo"], c["sistema"]) for c in categorias if c["sistema"]}
    assert ("Retirada para PF", "saida", True) in da_pj
    assert ("Pró-labore e lucros", "entrada", True) in da_pj
    assert sum(c["nome"] == "Retirada para PF" for c in categorias) == 1


def test_categoria_existente_de_mesmo_tipo_vira_sistema(
    client: TestClient, com_tipo: Callable[..., Conta]
) -> None:
    com_tipo("prestador")
    criada = ok(
        client.post("/api/v1/categorias", json={"nome": "pró-labore E LUCROS", "tipo": "entrada"}),
        201,
    )
    ok(client.patch(ME, json={"tem_pj": True}))

    categorias = {c["id"]: c for c in ok(client.get("/api/v1/categorias"))}
    assert categorias[criada["id"]]["sistema"] is True
    assert sum(c["nome"].lower() == "pró-labore e lucros" for c in categorias.values()) == 1


def test_categoria_de_tipo_diferente_impede_ligar(
    client: TestClient, com_tipo: Callable[..., Conta]
) -> None:
    com_tipo("prestador")
    ok(client.post("/api/v1/categorias", json={"nome": "Retirada para PF", "tipo": "entrada"}), 201)

    assert erro(client.patch(ME, json={"tem_pj": True}), 409)["codigo"] == "categoria_conflitante"
    assert ok(client.get(ME))["tem_pj"] is False


def test_pj_desligada_recusa_leitura_e_escrita(
    client: TestClient, com_tipo: Callable[..., Conta]
) -> None:
    conta = com_tipo("prestador")

    resposta = lancar(client, conta, "Renda extra", 1_000, carteira="pj")
    assert erro(resposta, 409)["codigo"] == "carteira_pj_desligada"
    resposta = client.get("/api/v1/ciclos/atual", params={"carteira": "pj"})
    assert erro(resposta, 409)["codigo"] == "carteira_pj_desligada"


# --- US1: saldo por carteira -----------------------------------------------------------------


def test_saldo_da_pj_do_carlos(client: TestClient, carlos: Conta) -> None:
    ok(lancar(client, carlos, "Renda extra", 800_000, carteira="pj"), 201)
    ok(lancar(client, carlos, "Outros", 7_500, carteira="pj"), 201)
    ok(lancar(client, carlos, "Outros", 30_000, carteira="pj"), 201)

    pj = resumo(client, "pj")
    assert (pj["entradas"], pj["saidas"], pj["saldo"]) == (800_000, 37_500, 762_500)
    assert pj["ciclo"]["inicio"] == "2026-10-01" and pj["ciclo"]["fim"] == "2026-10-31"
    assert resumo(client, "pf")["saldo"] == 0
    assert resumo(client)["saldo"] == 0


def test_cada_rota_mostra_so_a_carteira_pedida(client: TestClient, carlos: Conta) -> None:
    pf = ok(lancar(client, carlos, "Alimentação", 1_000), 201)
    pj = ok(lancar(client, carlos, "Outros", 2_000, carteira="pj"), 201)
    assert (pf["carteira"], pj["carteira"]) == ("pf", "pj")

    for carteira, esperado, outro in (("pf", pf, pj), (None, pf, pj), ("pj", pj, pf)):
        params = {"carteira": carteira} if carteira else {}
        ids = [
            lanc["id"]
            for lanc in ok(client.get("/api/v1/ciclos/2026-10-01/lancamentos", params=params))
        ]
        assert esperado["id"] in ids and outro["id"] not in ids
        assert resumo(client, carteira)["saidas"] == esperado["valor"]
        assert ok(client.get("/api/v1/ciclos/atual", params=params))["inicio"] == "2026-10-01"
        assert ok(client.get("/api/v1/ciclos/2026-10-10", params=params))["fim"] == "2026-10-31"


def test_ciclo_pj_anterior_so_com_lancamento_pj(
    client: TestClient, carlos: Conta, db: Session
) -> None:
    ok(lancar(client, carlos, "Alimentação", 1_000, data="2026-09-10"), 201)
    assert ok(client.get("/api/v1/ciclos/atual", params={"carteira": "pj"}))["anterior"] is None

    ok(lancar(client, carlos, "Outros", 1_000, data="2026-09-10", carteira="pj"), 201)
    atual = ok(client.get("/api/v1/ciclos/atual", params={"carteira": "pj"}))
    assert atual["anterior"] == "2026-09-01"


def test_clt_prestador_lanca_na_pj_sem_salario(
    client: TestClient, com_tipo: Callable[..., Conta]
) -> None:
    ana = com_tipo("clt_prestador", tem_pj=True)

    assert ok(lancar(client, ana, "Outros", 1_000, carteira="pj"), 201)["carteira"] == "pj"
    assert erro(lancar(client, ana, "Outros", 1_000), 409)["codigo"] == "salario_necessario"
    assert (
        ok(client.get("/api/v1/ciclos/atual", params={"carteira": "pj"}))["inicio"] == "2026-10-01"
    )
    assert client.get("/api/v1/ciclos/atual").status_code == 404


def test_salario_na_pj_e_recusado(client: TestClient, carlos: Conta) -> None:
    resposta = lancar(client, carlos, "Salário", 1_000, carteira="pj")

    assert "categoria_id" in erro(resposta, 422)["campos"]


def test_sem_carteira_e_pf(client: TestClient, carlos: Conta, db: Session) -> None:
    corpo = ok(lancar(client, carlos, "Alimentação", 1_000), 201)

    assert corpo["carteira"] == "pf"
    assert db.get(Lancamento, corpo["id"]).carteira == "pf"


def test_mudar_de_carteira_segue_a_carteira_de_destino(
    client: TestClient, com_tipo: Callable[..., Conta], db: Session
) -> None:
    ana = com_tipo("clt_prestador", tem_pj=True)
    ok(lancar(client, ana, "Salário", 500_000, data="2026-10-05"), 201)
    gasto = ok(lancar(client, ana, "Lazer", 2_000), 201)

    movido = ok(client.patch(f"{LANCAMENTOS}/{gasto['id']}", json={"carteira": "pj"}))
    assert movido["carteira"] == "pj"
    # Salário não vai para a PJ.
    salario = db.scalar(
        select(Lancamento.id).where(
            Lancamento.usuario_id == ana.usuario.id,
            Lancamento.categoria_id == ana.categorias["Salário"],
        )
    )
    resposta = client.patch(f"{LANCAMENTOS}/{salario}", json={"carteira": "pj"})
    assert "categoria_id" in erro(resposta, 422)["campos"]


def test_pj_nao_segura_o_unico_salario(client: TestClient, com_tipo: Callable[..., Conta]) -> None:
    ana = com_tipo("clt_prestador", tem_pj=True)
    salario = ok(lancar(client, ana, "Salário", 500_000, data="2026-10-05"), 201)
    ok(lancar(client, ana, "Outros", 1_000, carteira="pj"), 201)

    ok(client.delete(f"{LANCAMENTOS}/{salario['id']}"), 204)


def test_gasto_pj_nao_conta_no_limite_da_pf(client: TestClient, carlos: Conta) -> None:
    ok(client.patch(f"/api/v1/categorias/{carlos.categorias['Lazer']}", json={"limite": 10_000}))
    ok(lancar(client, carlos, "Lazer", 9_000, carteira="pj"), 201)

    pf = ok(lancar(client, carlos, "Lazer", 1_000), 201)
    assert pf["aviso_limite"] is None
    item = next(c for c in resumo(client, "pf")["saidas_por_categoria"] if c["nome"] == "Lazer")
    assert item["total"] == 1_000


def test_lancamento_pj_de_outro_usuario(
    client: TestClient,
    carlos: Conta,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
) -> None:
    pj = ok(lancar(client, carlos, "Outros", 1_000, carteira="pj"), 201)
    bia = novo_client()
    criar_conta(bia, "bia@exemplo.com")

    assert bia.get(f"{LANCAMENTOS}/{pj['id']}").status_code == 404
    assert bia.patch(f"{LANCAMENTOS}/{pj['id']}", json={"valor": 5}).status_code == 404
    assert bia.delete(f"{LANCAMENTOS}/{pj['id']}").status_code == 404


# --- US3: recorrências por carteira ----------------------------------------------------------


def recorrencia(client: TestClient, conta: Conta, **extra: Any) -> Any:
    corpo = {
        "descricao": "DAS",
        "valor": 7_500,
        "categoria_id": conta.categorias["Outros"],
        "dia": 20,
    }
    return client.post(RECORRENCIAS, json={**corpo, **extra})


def previstos(db: Session, conta: Conta, carteira: str) -> list[tuple[str, int]]:
    db.expire_all()
    return [
        (lanc.data.isoformat(), lanc.valor)
        for lanc in db.scalars(
            select(Lancamento).where(
                Lancamento.usuario_id == conta.usuario.id,
                Lancamento.recorrencia_id.is_not(None),
                Lancamento.carteira == carteira,
            )
        )
    ]


def test_recorrencia_pj_gera_um_previsto_por_mes(
    client: TestClient, carlos: Conta, db: Session
) -> None:
    rec = ok(recorrencia(client, carlos, carteira="pj"), 201)
    assert rec["carteira"] == "pj"
    for _ in range(2):
        ok(client.get("/api/v1/ciclos/atual", params={"carteira": "pj"}))

    assert previstos(db, carlos, "pj") == [("2026-10-20", 7_500)]
    assert previstos(db, carlos, "pf") == []


def test_recorrencia_pj_exige_a_pj(client: TestClient, com_tipo: Callable[..., Conta]) -> None:
    conta = com_tipo("prestador")

    assert erro(recorrencia(client, conta, carteira="pj"), 409)["codigo"] == "carteira_pj_desligada"
    assert ok(recorrencia(client, conta), 201)["carteira"] == "pf"


def test_salario_pf_nao_gera_previsto_pj(
    client: TestClient, com_tipo: Callable[..., Conta], db: Session
) -> None:
    ana = com_tipo("clt_prestador", tem_pj=True)
    ok(recorrencia(client, ana, carteira="pj"), 201)
    ok(recorrencia(client, ana, descricao="Aluguel", categoria_id=ana.categorias["Moradia"]), 201)
    ok(lancar(client, ana, "Salário", 500_000, data="2026-10-05"), 201)

    # O aluguel (PF) nasce com o salário; o DAS (PJ) nasceu com o mês e não duplica.
    assert previstos(db, ana, "pf") == [("2026-10-20", 7_500)]
    assert previstos(db, ana, "pj") == [("2026-10-20", 7_500)]


def test_listar_recorrencias_por_carteira(client: TestClient, carlos: Conta) -> None:
    ok(recorrencia(client, carlos, carteira="pj"), 201)
    ok(recorrencia(client, carlos, descricao="Internet"), 201)

    pj = ok(client.get(RECORRENCIAS, params={"carteira": "pj"}))
    todas = ok(client.get(RECORRENCIAS))
    assert [r["descricao"] for r in pj] == ["DAS"]
    assert len(todas) == 2


# --- US5: desligar a PJ e trocar o tipo de renda --------------------------------------------


def test_desligar_sem_dados(client: TestClient, carlos: Conta) -> None:
    assert ok(client.patch(ME, json={"tem_pj": False}))["tem_pj"] is False


@pytest.mark.parametrize("o_que", ["lancamento", "recorrencia"])
def test_desligar_ou_ir_para_clt_com_dados(client: TestClient, carlos: Conta, o_que: str) -> None:
    if o_que == "lancamento":
        ok(lancar(client, carlos, "Outros", 1_000, carteira="pj"), 201)
    else:
        ok(recorrencia(client, carlos, carteira="pj"), 201)

    assert erro(client.patch(ME, json={"tem_pj": False}), 409)["codigo"] == "pj_com_dados"
    assert erro(client.patch(ME, json={"tipo_renda": "clt"}), 409)["codigo"] == "pj_com_dados"
    assert ok(client.get(ME))["tem_pj"] is True


def test_ir_para_clt_sem_dados_desliga_a_pj(client: TestClient, carlos: Conta) -> None:
    corpo = ok(client.patch(ME, json={"tipo_renda": "clt"}))

    assert (corpo["tipo_renda"], corpo["tem_pj"]) == ("clt", False)


def test_troca_para_clt_prestador_ignora_a_pj(client: TestClient, carlos: Conta) -> None:
    ok(lancar(client, carlos, "Outros", 1_000, carteira="pj"), 201)

    corpo = ok(client.patch(ME, json={"tipo_renda": "clt_prestador"}))
    assert (corpo["tipo_renda"], corpo["tem_pj"]) == ("clt_prestador", True)


def test_troca_para_clt_prestador_ainda_olha_a_pf(client: TestClient, carlos: Conta) -> None:
    ok(lancar(client, carlos, "Alimentação", 1_000), 201)  # PF sem salário

    resposta = client.patch(ME, json={"tipo_renda": "clt_prestador"})
    assert resposta.status_code == 409
