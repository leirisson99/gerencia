from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/dividas"


@pytest.fixture(autouse=True)
def hoje_15_de_janeiro_de_2027(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2027, 1, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


@pytest.fixture
def salario(client: TestClient, conta: Conta) -> None:
    resposta = client.post(
        "/api/v1/lancamentos",
        json={"valor": 500_000, "categoria_id": conta.categorias["Salário"], "data": "2026-10-05"},
    )
    assert resposta.status_code == 201


def cadastrar(client: TestClient, conta: Conta, **alteracoes: Any) -> httpx.Response:
    dados: dict[str, Any] = {
        "descricao": "Notebook",
        "pessoa": "Loja X",
        "direcao": "devo",
        "valor_total": 100_000,
        "parcelas": 3,
        "forma_pagamento": "pix",
        "dia_vencimento": 15,
        "data_inicio": "2026-10-05",
        "categoria_id": conta.categorias["Outros"],
    }
    categoria = alteracoes.pop("categoria", None)
    if categoria:
        dados["categoria_id"] = conta.categorias[categoria]
    dados.update(alteracoes)
    return client.post(URL, json=dados)


def pagar(client: TestClient, lancamento_id: int) -> httpx.Response:
    return client.patch(f"/api/v1/lancamentos/{lancamento_id}", json={"status": "realizado"})


# --- US1: cadastrar e gerar parcelas -------------------------------------------------------


def test_cadastra_e_gera_as_parcelas(client: TestClient, conta: Conta, salario: None) -> None:
    resposta = cadastrar(client, conta)

    assert resposta.status_code == 201
    divida = resposta.json()
    assert (divida["parcelas_pagas"], divida["valor_pago"], divida["valor_restante"]) == (
        0,
        0,
        100_000,
    )
    assert divida["quitada"] is False
    parcelas = divida["lancamentos"]
    assert [(p["parcela_num"], p["data"], p["valor"]) for p in parcelas] == [
        (1, "2026-10-15", 33_333),
        (2, "2026-11-15", 33_333),
        (3, "2026-12-15", 33_334),
    ]
    assert all(p["status"] == "previsto" and p["tipo"] == "saida" for p in parcelas)
    assert all(p["divida_id"] == divida["id"] and p["conta_no_saldo"] for p in parcelas)
    assert all(p["descricao"] == "Notebook (1/3)" for p in parcelas[:1])


def test_parcelas_aparecem_nos_ciclos(client: TestClient, conta: Conta, salario: None) -> None:
    cadastrar(client, conta)
    lancamentos = client.get("/api/v1/ciclos/2026-10-05/lancamentos").json()
    assert [lanc["parcela_num"] for lanc in lancamentos if lanc["divida_id"]] == [1, 2, 3]


def test_me_devem_gera_entradas(client: TestClient, conta: Conta, salario: None) -> None:
    resposta = cadastrar(
        client,
        conta,
        descricao="Empréstimo",
        pessoa="João",
        direcao="me_devem",
        valor_total=30_000,
        parcelas=2,
        categoria="Renda extra",
    )

    assert resposta.status_code == 201
    assert [p["tipo"] for p in resposta.json()["lancamentos"]] == ["entrada", "entrada"]


def test_cartao_nao_conta_no_saldo(client: TestClient, conta: Conta, salario: None) -> None:
    divida = cadastrar(client, conta, forma_pagamento="cartao").json()

    assert all(p["conta_no_saldo"] is False for p in divida["lancamentos"])
    assert pagar(client, divida["lancamentos"][0]["id"]).status_code == 200
    resumo = client.get("/api/v1/ciclos/2026-10-05/resumo").json()
    assert resumo["saidas"] == 0
    assert client.get(f"{URL}/{divida['id']}").json()["parcelas_pagas"] == 1


def test_sem_salario(client: TestClient, conta: Conta) -> None:
    resposta = cadastrar(client, conta)
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "salario_necessario"


def test_inicio_antes_do_primeiro_ciclo(client: TestClient, conta: Conta, salario: None) -> None:
    resposta = cadastrar(client, conta, data_inicio="2026-09-01", dia_vencimento=10)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "antes_do_primeiro_ciclo"
    assert client.get(URL).json() == []


@pytest.mark.parametrize(
    ("campo", "alteracoes"),
    [
        ("categoria_id", {"categoria": "Renda extra"}),  # devo em categoria de entrada
        ("categoria_id", {"direcao": "me_devem"}),  # me devem em categoria de saída
        ("categoria_id", {"categoria": "Salário"}),
        (
            "forma_pagamento",
            {"direcao": "me_devem", "categoria": "Renda extra", "forma_pagamento": "cartao"},
        ),
        ("forma_pagamento", {"forma_pagamento": "cheque"}),
        ("direcao", {"direcao": "emprestei"}),
        ("parcelas", {"parcelas": 0}),
        ("parcelas", {"parcelas": 121}),
        ("valor_total", {"valor_total": 2, "parcelas": 3}),
        ("valor_total", {"valor_total": 10.5}),
        ("dia_vencimento", {"dia_vencimento": 32}),
        ("pessoa", {"pessoa": "  "}),
        ("descricao", {"descricao": ""}),
    ],
)
def test_validacao(
    client: TestClient, conta: Conta, salario: None, campo: str, alteracoes: dict
) -> None:
    resposta = cadastrar(client, conta, **alteracoes)

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_categoria_de_outro_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
    salario: None,
) -> None:
    bia = criar_conta(novo_client(), email="bia@exemplo.com")
    resposta = cadastrar(client, conta, categoria_id=bia.categorias["Outros"])
    assert resposta.status_code == 404


def test_cento_e_vinte_parcelas(client: TestClient, conta: Conta, salario: None) -> None:
    resposta = cadastrar(client, conta, valor_total=1_200_001, parcelas=120)

    assert resposta.status_code == 201
    parcelas = resposta.json()["lancamentos"]
    assert len(parcelas) == 120
    assert sum(p["valor"] for p in parcelas) == 1_200_001
    assert parcelas[-1]["data"] == "2036-09-15"


# --- US2 e US3: pagar e acompanhar ---------------------------------------------------------


def test_pagar_parcela_conta_no_saldo_e_na_situacao(
    client: TestClient, conta: Conta, salario: None
) -> None:
    divida = cadastrar(client, conta).json()

    assert pagar(client, divida["lancamentos"][0]["id"]).status_code == 200

    atual = client.get(f"{URL}/{divida['id']}").json()
    assert (atual["parcelas_pagas"], atual["valor_pago"], atual["valor_restante"]) == (
        1,
        33_333,
        66_667,
    )
    resumo = client.get("/api/v1/ciclos/2026-10-05/resumo").json()
    assert resumo["saidas"] == 33_333


def test_quitada(client: TestClient, conta: Conta, salario: None) -> None:
    divida = cadastrar(client, conta, parcelas=2, valor_total=10_000).json()
    for parcela in divida["lancamentos"]:
        pagar(client, parcela["id"])

    assert client.get(f"{URL}/{divida['id']}").json()["quitada"] is True


def test_lista_as_dividas(client: TestClient, conta: Conta, salario: None) -> None:
    cadastrar(client, conta, descricao="Notebook")
    cadastrar(client, conta, descricao="Celular", parcelas=1)

    assert [d["descricao"] for d in client.get(URL).json()] == ["Notebook", "Celular"]


def test_parcela_nao_pode_ser_excluida(client: TestClient, conta: Conta, salario: None) -> None:
    parcela = cadastrar(client, conta).json()["lancamentos"][0]

    resposta = client.delete(f"/api/v1/lancamentos/{parcela['id']}")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "parcela_de_divida"


def test_parcela_nao_troca_de_categoria(client: TestClient, conta: Conta, salario: None) -> None:
    parcela = cadastrar(client, conta).json()["lancamentos"][0]

    resposta = client.patch(
        f"/api/v1/lancamentos/{parcela['id']}", json={"categoria_id": conta.categorias["Lazer"]}
    )

    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["erro"]["campos"]


def test_parcela_aceita_ajuste_de_valor_e_data(
    client: TestClient, conta: Conta, salario: None
) -> None:
    divida = cadastrar(client, conta).json()
    parcela = divida["lancamentos"][0]

    resposta = client.patch(
        f"/api/v1/lancamentos/{parcela['id']}",
        json={"valor": 34_000, "data": "2026-10-16", "status": "realizado"},
    )

    assert resposta.status_code == 200
    assert client.get(f"{URL}/{divida['id']}").json()["valor_pago"] == 34_000


def test_divida_de_outro_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
    salario: None,
) -> None:
    divida = cadastrar(client, conta).json()
    outro = novo_client()
    criar_conta(outro, email="bia@exemplo.com")

    assert outro.get(f"{URL}/{divida['id']}").status_code == 404
    assert outro.get(URL).json() == []


def test_exige_login(client: TestClient) -> None:
    assert client.get(URL).status_code == 401
