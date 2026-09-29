from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/cartelas"


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
        json={"valor": 500_000, "categoria_id": conta.categorias["Salário"], "data": "2027-01-05"},
    )
    assert resposta.status_code == 201


def criar(client: TestClient, **dados: Any) -> httpx.Response:
    return client.post(URL, json={"nome": "Viagem", "meta": 100_000, **dados})


def casa_de(cartela: dict[str, Any], valor: int, ajuste: bool = False) -> dict[str, Any]:
    return next(c for c in cartela["casas"] if c["valor"] == valor and c["is_ajuste"] == ajuste)


def depositar(client: TestClient, cartela: dict[str, Any], casa: dict[str, Any]) -> httpx.Response:
    return client.post(f"{URL}/{cartela['id']}/casas/{casa['id']}/deposito")


def desfazer(client: TestClient, cartela: dict[str, Any], casa: dict[str, Any]) -> httpx.Response:
    return client.delete(f"{URL}/{cartela['id']}/casas/{casa['id']}/deposito")


# --- US1: criar ----------------------------------------------------------------------------


def test_cria_com_base_padrao_e_casa_de_ajuste(client: TestClient, conta: Conta) -> None:
    resposta = criar(client)

    assert resposta.status_code == 201
    cartela = resposta.json()
    assert (cartela["nome"], cartela["meta"], cartela["valor_base"]) == ("Viagem", 100_000, 100)
    normais = [c for c in cartela["casas"] if not c["is_ajuste"]]
    assert [c["valor"] for c in normais] == [k * 100 for k in range(1, 45)]
    assert [c["valor"] for c in cartela["casas"] if c["is_ajuste"]] == [1_000]
    assert sum(c["valor"] for c in cartela["casas"]) == 100_000
    assert (cartela["guardado"], cartela["falta"], cartela["percentual"]) == (0, 100_000, 0)
    assert cartela["maior_casa_livre"] == 4_400
    assert all(c["depositado_em"] is None and c["lancamento_id"] is None for c in cartela["casas"])


def test_cria_com_base_de_5_reais(client: TestClient, conta: Conta) -> None:
    cartela = criar(client, meta=500_000, valor_base=500).json()
    assert len(cartela["casas"]) == 45
    assert cartela["casas"][43]["valor"] == 22_000


@pytest.mark.parametrize(
    ("campo", "dados"),
    [
        ("meta", {"meta": 50, "valor_base": 100}),
        ("meta", {"meta": 10.5}),
        ("meta", {"meta": 0}),
        ("valor_base", {"valor_base": 0}),
        ("meta", {"meta": 99_999_999_999, "valor_base": 1}),  # casas demais
        ("nome", {"nome": "  "}),
    ],
)
def test_validacao(client: TestClient, conta: Conta, campo: str, dados: dict) -> None:
    resposta = criar(client, **dados)

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_lista_e_consulta(client: TestClient, conta: Conta) -> None:
    viagem = criar(client).json()
    criar(client, nome="Reserva", meta=10_000)

    assert [c["nome"] for c in client.get(URL).json()] == ["Viagem", "Reserva"]
    assert client.get(f"{URL}/{viagem['id']}").json() == viagem


# --- US2: depositar e desfazer -------------------------------------------------------------


def test_deposito_gera_saida_em_poupanca(client: TestClient, conta: Conta, salario: None) -> None:
    cartela = criar(client).json()

    resposta = depositar(client, cartela, casa_de(cartela, 3_000))

    assert resposta.status_code == 200
    casa = casa_de(resposta.json(), 3_000)
    assert casa["depositado_em"] == "2027-01-15"
    lancamento = client.get(f"/api/v1/lancamentos/{casa['lancamento_id']}").json()
    assert (lancamento["valor"], lancamento["tipo"], lancamento["status"], lancamento["data"]) == (
        3_000,
        "saida",
        "realizado",
        "2027-01-15",
    )
    assert lancamento["categoria_id"] == conta.categorias["Poupança"]
    resumo = client.get("/api/v1/ciclos/2027-01-05/resumo").json()
    assert resumo["saidas_por_categoria"] == [
        {"categoria_id": conta.categorias["Poupança"], "nome": "Poupança", "total": 3_000}
    ]


def test_depositos_em_qualquer_ordem_e_progresso(
    client: TestClient, conta: Conta, salario: None
) -> None:
    cartela = criar(client).json()
    depositar(client, cartela, casa_de(cartela, 4_400))
    atual = depositar(client, cartela, casa_de(cartela, 1_000, ajuste=True)).json()

    assert (atual["guardado"], atual["falta"], atual["percentual"]) == (5_400, 94_600, 5)
    assert atual["maior_casa_livre"] == 4_300


def test_deposito_repetido(client: TestClient, conta: Conta, salario: None) -> None:
    cartela = criar(client).json()
    depositar(client, cartela, casa_de(cartela, 100))

    resposta = depositar(client, cartela, casa_de(cartela, 100))

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "casa_depositada"


def test_desfazer_deposito(client: TestClient, conta: Conta, salario: None) -> None:
    cartela = criar(client).json()
    lancamento_id = casa_de(depositar(client, cartela, casa_de(cartela, 200)).json(), 200)[
        "lancamento_id"
    ]

    resposta = desfazer(client, cartela, casa_de(cartela, 200))

    assert resposta.status_code == 200
    assert casa_de(resposta.json(), 200)["depositado_em"] is None
    assert resposta.json()["guardado"] == 0
    assert client.get(f"/api/v1/lancamentos/{lancamento_id}").status_code == 404


def test_desfazer_casa_livre(client: TestClient, conta: Conta, salario: None) -> None:
    cartela = criar(client).json()
    resposta = desfazer(client, cartela, casa_de(cartela, 200))
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "casa_livre"


def test_completa(client: TestClient, conta: Conta, salario: None) -> None:
    cartela = criar(client, meta=600).json()  # casas 1, 2, 3
    for casa in cartela["casas"]:
        atual = depositar(client, cartela, casa).json()

    assert (atual["percentual"], atual["falta"], atual["maior_casa_livre"]) == (100, 0, None)


def test_deposito_sem_salario(client: TestClient, conta: Conta) -> None:
    cartela = criar(client).json()

    resposta = depositar(client, cartela, casa_de(cartela, 100))

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "salario_necessario"
    assert client.get(f"{URL}/{cartela['id']}").json()["guardado"] == 0


def test_lancamento_do_deposito_e_protegido(
    client: TestClient, conta: Conta, salario: None
) -> None:
    cartela = criar(client).json()
    casa = casa_de(depositar(client, cartela, casa_de(cartela, 500)).json(), 500)
    caminho = f"/api/v1/lancamentos/{casa['lancamento_id']}"

    excluir = client.delete(caminho)
    assert excluir.status_code == 409
    assert excluir.json()["erro"]["codigo"] == "deposito_de_cartela"
    for mudanca in (
        {"valor": 1},
        {"status": "previsto"},
        {"categoria_id": conta.categorias["Lazer"]},
    ):
        assert client.patch(caminho, json=mudanca).status_code == 422
    assert client.patch(caminho, json={"descricao": "Guardei"}).status_code == 200


def test_poupanca_e_categoria_do_sistema(client: TestClient, conta: Conta) -> None:
    resposta = client.patch(
        f"/api/v1/categorias/{conta.categorias['Poupança']}", json={"nome": "Reserva"}
    )
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "categoria_do_sistema"


# --- Isolamento ----------------------------------------------------------------------------


def test_cartela_de_outro_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
    salario: None,
) -> None:
    cartela = criar(client).json()
    outro = novo_client()
    criar_conta(outro, email="bia@exemplo.com")

    assert outro.get(f"{URL}/{cartela['id']}").status_code == 404
    assert depositar(outro, cartela, cartela["casas"][0]).status_code == 404
    assert outro.get(URL).json() == []


def test_casa_de_outra_cartela(client: TestClient, conta: Conta, salario: None) -> None:
    viagem = criar(client).json()
    reserva = criar(client, nome="Reserva").json()

    resposta = depositar(client, viagem, reserva["casas"][0])

    assert resposta.status_code == 404


def test_exige_login(client: TestClient) -> None:
    assert client.get(URL).status_code == 401
