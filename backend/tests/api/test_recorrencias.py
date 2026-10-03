from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Categoria
from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/recorrencias"


@pytest.fixture(autouse=True)
def hoje_15_de_janeiro_de_2027(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2027, 1, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


def lancar(client: TestClient, conta: Conta, categoria: str, data: str, valor: int = 500_000):
    resposta = client.post(
        "/api/v1/lancamentos",
        json={"valor": valor, "categoria_id": conta.categorias[categoria], "data": data},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def recorrencia(
    client: TestClient,
    conta: Conta,
    descricao: str = "Internet",
    dia: int = 10,
    valor: int = 10_000,
    categoria: str = "Moradia",
    **extra: Any,
) -> httpx.Response:
    return client.post(
        URL,
        json={
            "descricao": descricao,
            "valor": valor,
            "categoria_id": conta.categorias[categoria],
            "dia": dia,
            **extra,
        },
    )


def gerados(client: TestClient, data_ciclo: str) -> list[dict[str, Any]]:
    lancamentos = client.get(f"/api/v1/ciclos/{data_ciclo}/lancamentos").json()
    return [lanc for lanc in lancamentos if lanc["recorrencia_id"] is not None]


# --- US1: cadastrar ------------------------------------------------------------------------


def test_cadastro_com_ciclo_aberto_gera_o_previsto(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05")

    resposta = recorrencia(client, conta)

    assert resposta.status_code == 201
    rec = resposta.json()
    assert rec == {
        "id": rec["id"],
        "descricao": "Internet",
        "valor": 10_000,
        "tipo": "saida",
        "categoria_id": conta.categorias["Moradia"],
        "dia": 10,
        "ativa": True,
        "carteira": "pf",
    }
    [previsto] = gerados(client, "2026-10-05")
    assert (previsto["data"], previsto["valor"], previsto["status"]) == (
        "2026-10-10",
        10_000,
        "previsto",
    )
    assert (previsto["recorrencia_id"], previsto["descricao"], previsto["tipo"]) == (
        rec["id"],
        "Internet",
        "saida",
    )


def test_dia_que_ja_passou_vai_para_o_mes_seguinte(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05")
    recorrencia(client, conta, descricao="Aluguel", dia=1, valor=150_000)

    assert [p["data"] for p in gerados(client, "2026-10-05")] == ["2026-11-01"]


def test_sem_ciclo_nao_gera(client: TestClient, conta: Conta) -> None:
    assert recorrencia(client, conta).status_code == 201
    lancar(client, conta, "Salário", "2026-10-05")
    # O salário abre o ciclo e gera o previsto uma única vez.
    assert len(gerados(client, "2026-10-05")) == 1


def test_previsto_nao_entra_no_saldo(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05")
    recorrencia(client, conta)

    resumo = client.get("/api/v1/ciclos/2026-10-05/resumo").json()

    assert (resumo["saidas"], resumo["saldo"]) == (0, 500_000)


def test_recorrencia_de_entrada(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05")
    recorrencia(client, conta, descricao="Aluguel recebido", categoria="Renda extra", dia=15)

    [previsto] = gerados(client, "2026-10-05")
    assert previsto["tipo"] == "entrada"


@pytest.mark.parametrize(
    ("campo", "alteracoes"),
    [
        ("categoria_id", {"categoria": "Salário"}),
        ("dia", {"dia": 0}),
        ("dia", {"dia": 32}),
        ("valor", {"valor": 10.5}),
        ("valor", {"valor": 0}),
        ("descricao", {"descricao": "   "}),
        ("descricao", {"descricao": "x" * 201}),
        ("tipo", {"tipo": "saida"}),
    ],
)
def test_validacao(client: TestClient, conta: Conta, campo: str, alteracoes: dict) -> None:
    resposta = recorrencia(client, conta, **alteracoes)

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_categoria_inativa(client: TestClient, conta: Conta, db: Session) -> None:
    db.execute(
        update(Categoria).where(Categoria.id == conta.categorias["Lazer"]).values(ativa=False)
    )
    db.commit()

    resposta = recorrencia(client, conta, categoria="Lazer")

    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["erro"]["campos"]


def test_categoria_de_outro_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    bia = criar_conta(novo_client(), email="bia@exemplo.com")

    resposta = recorrencia(client, bia)

    assert resposta.status_code == 404


# --- US2: gerar ao abrir o ciclo -------------------------------------------------------------


@pytest.fixture
def internet_e_aluguel(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05")
    recorrencia(client, conta, descricao="Internet", dia=10)
    recorrencia(client, conta, descricao="Aluguel", dia=1, valor=150_000)


def test_salario_novo_gera_os_previstos_do_ciclo(
    client: TestClient, conta: Conta, internet_e_aluguel: None
) -> None:
    lancar(client, conta, "Salário", "2026-11-06")

    previstos = gerados(client, "2026-11-06")

    assert sorted((p["descricao"], p["data"]) for p in previstos) == [
        ("Aluguel", "2026-12-01"),
        ("Internet", "2026-11-10"),
    ]


def test_previsto_pendente_fica_no_ciclo_anterior(
    client: TestClient, conta: Conta, internet_e_aluguel: None
) -> None:
    antes = gerados(client, "2026-10-05")

    lancar(client, conta, "Salário", "2026-11-06")

    # O aluguel de 01/11 caía no ciclo aberto; agora pertence ao novo ciclo pela data.
    assert [p for p in gerados(client, "2026-10-05") if p["data"] < "2026-11-06"] == [
        p for p in antes if p["data"] < "2026-11-06"
    ]
    datas = sorted(p["data"] for p in gerados(client, "2026-10-05") + gerados(client, "2026-11-06"))
    assert datas == ["2026-10-10", "2026-11-01", "2026-11-10", "2026-12-01"]


def test_recorrencia_desativada_nao_gera(
    client: TestClient, conta: Conta, internet_e_aluguel: None
) -> None:
    internet = next(r for r in client.get(URL).json() if r["descricao"] == "Internet")
    client.patch(f"{URL}/{internet['id']}", json={"ativa": False})

    lancar(client, conta, "Salário", "2026-11-06")

    assert [p["descricao"] for p in gerados(client, "2026-11-06")] == ["Aluguel"]


def test_salario_retroativo_nao_gera(
    client: TestClient, conta: Conta, internet_e_aluguel: None
) -> None:
    lancar(client, conta, "Salário", "2026-09-05")

    assert gerados(client, "2026-09-05") == []


def test_segundo_salario_na_mesma_data_nao_duplica(
    client: TestClient, conta: Conta, internet_e_aluguel: None
) -> None:
    lancar(client, conta, "Salário", "2026-11-06")
    lancar(client, conta, "Salário", "2026-11-06", 10_000)

    assert len(gerados(client, "2026-11-06")) == 2


# --- US3: confirmar ------------------------------------------------------------------------


def test_confirmar_pagamento_entra_no_saldo(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05")
    recorrencia(client, conta)
    [previsto] = gerados(client, "2026-10-05")

    resposta = client.patch(
        f"/api/v1/lancamentos/{previsto['id']}", json={"status": "realizado", "valor": 11_000}
    )

    assert resposta.status_code == 200
    resumo = client.get("/api/v1/ciclos/2026-10-05/resumo").json()
    assert resumo["saidas"] == 11_000
    assert resumo["saidas_por_categoria"][0]["nome"] == "Moradia"


# --- US4: alterar e desativar --------------------------------------------------------------


def test_alterar_vale_so_para_os_proximos_ciclos(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05")
    rec = recorrencia(client, conta).json()

    resposta = client.patch(f"{URL}/{rec['id']}", json={"valor": 12_000, "dia": 12})

    assert resposta.status_code == 200
    assert (resposta.json()["valor"], resposta.json()["dia"]) == (12_000, 12)
    assert [p["valor"] for p in gerados(client, "2026-10-05")] == [10_000]
    lancar(client, conta, "Salário", "2026-11-06")
    [novo] = gerados(client, "2026-11-06")
    assert (novo["valor"], novo["data"]) == (12_000, "2026-11-12")


def test_trocar_categoria_troca_o_tipo(client: TestClient, conta: Conta) -> None:
    rec = recorrencia(client, conta).json()

    resposta = client.patch(
        f"{URL}/{rec['id']}", json={"categoria_id": conta.categorias["Renda extra"]}
    )

    assert resposta.json()["tipo"] == "entrada"


@pytest.mark.parametrize("campo", ["descricao", "valor", "categoria_id", "dia", "ativa"])
def test_patch_nao_aceita_null(client: TestClient, conta: Conta, campo: str) -> None:
    rec = recorrencia(client, conta).json()

    resposta = client.patch(f"{URL}/{rec['id']}", json={campo: None})

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_patch_para_salario_e_recusado(client: TestClient, conta: Conta) -> None:
    rec = recorrencia(client, conta).json()

    resposta = client.patch(
        f"{URL}/{rec['id']}", json={"categoria_id": conta.categorias["Salário"]}
    )

    assert resposta.status_code == 422


def test_lista_so_as_do_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    outro = novo_client()
    bia = criar_conta(outro, email="bia@exemplo.com")
    recorrencia(outro, bia, descricao="Da Bia")
    rec_bia = outro.get(URL).json()[0]
    recorrencia(client, conta, descricao="Aluguel", dia=1)
    recorrencia(client, conta, descricao="Internet", dia=10)

    assert [r["descricao"] for r in client.get(URL).json()] == ["Aluguel", "Internet"]
    assert client.patch(f"{URL}/{rec_bia['id']}", json={"valor": 1}).status_code == 404


def test_exige_login(client: TestClient) -> None:
    assert client.get(URL).status_code == 401
    assert client.post(URL, json={}).status_code == 401
