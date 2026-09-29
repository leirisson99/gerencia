from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/ciclos"


@pytest.fixture(autouse=True)
def hoje_15_de_janeiro_de_2027(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2027, 1, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


def lancar(client: TestClient, conta: Conta, categoria: str, data: str, valor: int = 10_000):
    resposta = client.post(
        "/api/v1/lancamentos",
        json={"valor": valor, "categoria_id": conta.categorias[categoria], "data": data},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


@pytest.fixture
def tres_salarios(client: TestClient, conta: Conta) -> None:
    for data in ("2026-10-05", "2026-11-06", "2026-12-05"):
        lancar(client, conta, "Salário", data, 500_000)


def test_sem_salario_nao_ha_ciclo_atual(client: TestClient, conta: Conta) -> None:
    resposta = client.get(f"{URL}/atual")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "sem_ciclo"


def test_ciclo_atual_e_o_mais_recente(client: TestClient, tres_salarios: None) -> None:
    resposta = client.get(f"{URL}/atual")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "inicio": "2026-12-05",
        "fim": None,
        "aberto": True,
        "anterior": "2026-11-06",
        "proximo": None,
    }


def test_ciclo_do_meio_com_vizinhos(client: TestClient, tres_salarios: None) -> None:
    assert client.get(f"{URL}/2026-11-20").json() == {
        "inicio": "2026-11-06",
        "fim": "2026-12-04",
        "aberto": False,
        "anterior": "2026-10-05",
        "proximo": "2026-12-05",
    }


def test_navegar_anterior_e_proximo_volta_ao_mesmo_ciclo(
    client: TestClient, tres_salarios: None
) -> None:
    meio = client.get(f"{URL}/2026-11-20").json()

    anterior = client.get(f"{URL}/{meio['anterior']}").json()
    de_volta = client.get(f"{URL}/{anterior['proximo']}").json()

    assert (anterior["inicio"], anterior["fim"]) == ("2026-10-05", "2026-11-05")
    assert de_volta == meio


def test_primeiro_ciclo_nao_tem_anterior(client: TestClient, tres_salarios: None) -> None:
    assert client.get(f"{URL}/2026-10-05").json()["anterior"] is None


def test_data_antes_do_primeiro_salario(client: TestClient, tres_salarios: None) -> None:
    resposta = client.get(f"{URL}/2026-10-04")

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "sem_ciclo"


def test_data_invalida(client: TestClient, conta: Conta) -> None:
    resposta = client.get(f"{URL}/2026-13-01")
    assert resposta.status_code == 422


def test_virada_de_ano(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-12-20")
    lancar(client, conta, "Salário", "2027-01-15")

    assert client.get(f"{URL}/2027-01-10").json()["fim"] == "2027-01-14"


def test_lancamentos_do_ciclo(client: TestClient, conta: Conta, tres_salarios: None) -> None:
    fora_antes = lancar(client, conta, "Alimentação", "2026-11-05")
    depois = lancar(client, conta, "Moradia", "2026-12-04", 150_000)
    antes = lancar(client, conta, "Alimentação", "2026-11-10")
    fora_depois = lancar(client, conta, "Lazer", "2026-12-05")

    resposta = client.get(f"{URL}/2026-11-20/lancamentos")

    assert resposta.status_code == 200
    datas_ids = [(lanc["data"], lanc["id"]) for lanc in resposta.json()]
    assert datas_ids[1:] == [("2026-11-10", antes["id"]), ("2026-12-04", depois["id"])]
    assert datas_ids[0][0] == "2026-11-06"  # o salário que abre o ciclo
    ids = {lanc["id"] for lanc in resposta.json()}
    assert fora_antes["id"] not in ids
    assert fora_depois["id"] not in ids


def test_lancamentos_de_data_sem_ciclo(client: TestClient, conta: Conta) -> None:
    resposta = client.get(f"{URL}/2026-10-05/lancamentos")
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "sem_ciclo"


def test_salarios_de_outro_usuario_nao_criam_ciclos(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    outro = novo_client()
    bia = criar_conta(outro, email="bia@exemplo.com")
    lancar(outro, bia, "Salário", "2026-10-05")
    lancar(outro, bia, "Alimentação", "2026-10-06")

    assert client.get(f"{URL}/atual").status_code == 404
    lancar(client, conta, "Salário", "2026-11-01")
    lancamentos = client.get(f"{URL}/2026-11-01/lancamentos").json()
    assert [lanc["data"] for lanc in lancamentos] == ["2026-11-01"]


# --- Sugestão do valor do salário (FR-012) ----------------------------------------------


def test_sugestao_sem_salario(client: TestClient, conta: Conta) -> None:
    resposta = client.get("/api/v1/salarios/sugestao")
    assert resposta.status_code == 200
    assert resposta.json() == {"valor": None}


def test_sugestao_usa_o_salario_de_data_mais_recente(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-11-06", 520_000)
    lancar(client, conta, "Salário", "2026-10-05", 500_000)  # lançado depois, data anterior

    assert client.get("/api/v1/salarios/sugestao").json() == {"valor": 520_000}


def test_sugestao_ignora_outras_entradas(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05", 500_000)
    lancar(client, conta, "Renda extra", "2026-10-20", 900_000)

    assert client.get("/api/v1/salarios/sugestao").json() == {"valor": 500_000}


@pytest.mark.parametrize("caminho", ["/ciclos/atual", "/ciclos/2026-10-05", "/salarios/sugestao"])
def test_exige_login(client: TestClient, caminho: str) -> None:
    assert client.get(f"/api/v1{caminho}").status_code == 401
