from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Categoria, Lancamento
from tests.conftest import Conta, RelogioFixo


@pytest.fixture(autouse=True)
def hoje_15_de_janeiro_de_2027(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2027, 1, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


def lancar(
    client: TestClient, conta: Conta, categoria: str, data: str, valor: int, **extra: Any
) -> dict[str, Any]:
    resposta = client.post(
        "/api/v1/lancamentos",
        json={"valor": valor, "categoria_id": conta.categorias[categoria], "data": data, **extra},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def resumo(client: TestClient, data: str = "2026-10-05") -> dict[str, Any]:
    resposta = client.get(f"/api/v1/ciclos/{data}/resumo")
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


@pytest.fixture
def ciclo_de_outubro(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05", 500_000)
    lancar(client, conta, "Renda extra", "2026-10-20", 30_000)
    lancar(client, conta, "Alimentação", "2026-10-10", 80_000)
    lancar(client, conta, "Moradia", "2026-10-06", 150_000)
    lancar(client, conta, "Salário", "2026-11-06", 500_000)  # fecha o ciclo em 05/11


def test_totais_do_ciclo(client: TestClient, conta: Conta, ciclo_de_outubro: None) -> None:
    corpo = resumo(client)

    assert (corpo["entradas"], corpo["saidas"], corpo["saldo"]) == (530_000, 230_000, 300_000)
    assert corpo["ciclo"] == {
        "inicio": "2026-10-05",
        "fim": "2026-11-05",
        "aberto": False,
        "anterior": None,
        "proximo": "2026-11-06",
    }


def test_qualquer_data_do_ciclo_da_o_mesmo_resumo(
    client: TestClient, conta: Conta, ciclo_de_outubro: None
) -> None:
    assert resumo(client, "2026-10-31") == resumo(client, "2026-10-05")


def test_gasto_previsto_nao_muda_o_resumo(
    client: TestClient, conta: Conta, ciclo_de_outubro: None
) -> None:
    antes = resumo(client)
    lancar(client, conta, "Lazer", "2026-10-15", 10_000, status="previsto")
    assert resumo(client) == antes


def test_lancamento_fora_do_saldo_nao_conta(
    client: TestClient, conta: Conta, ciclo_de_outubro: None, db: Session
) -> None:
    antes = resumo(client)
    parcela = lancar(client, conta, "Lazer", "2026-10-15", 10_000)
    db.execute(
        update(Lancamento).where(Lancamento.id == parcela["id"]).values(conta_no_saldo=False)
    )
    db.commit()

    assert resumo(client) == antes


def test_saldo_negativo(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05", 100_000)
    lancar(client, conta, "Moradia", "2026-10-06", 150_000)

    assert resumo(client)["saldo"] == -50_000


def test_so_conta_lancamentos_do_ciclo(
    client: TestClient, conta: Conta, ciclo_de_outubro: None
) -> None:
    lancar(client, conta, "Alimentação", "2026-11-06", 99_000)  # próximo ciclo

    corpo = resumo(client)

    assert corpo["saidas"] == 230_000
    assert resumo(client, "2026-11-06")["saidas"] == 99_000


def test_gasto_por_categoria_do_maior_para_o_menor(
    client: TestClient, conta: Conta, ciclo_de_outubro: None
) -> None:
    lancar(client, conta, "Alimentação", "2026-10-11", 20_000)

    corpo = resumo(client)

    assert corpo["saidas_por_categoria"] == [
        {"categoria_id": conta.categorias["Moradia"], "nome": "Moradia", "total": 150_000},
        {"categoria_id": conta.categorias["Alimentação"], "nome": "Alimentação", "total": 100_000},
    ]
    assert corpo["entradas_por_categoria"] == [
        {"categoria_id": conta.categorias["Salário"], "nome": "Salário", "total": 500_000},
        {"categoria_id": conta.categorias["Renda extra"], "nome": "Renda extra", "total": 30_000},
    ]


def test_somas_por_categoria_fecham_com_os_totais(
    client: TestClient, conta: Conta, ciclo_de_outubro: None
) -> None:
    corpo = resumo(client)
    assert sum(c["total"] for c in corpo["saidas_por_categoria"]) == corpo["saidas"]
    assert sum(c["total"] for c in corpo["entradas_por_categoria"]) == corpo["entradas"]


def test_empate_em_ordem_alfabetica(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05", 500_000)
    lancar(client, conta, "Transporte", "2026-10-06", 5_000)
    lancar(client, conta, "Lazer", "2026-10-06", 5_000)
    lancar(client, conta, "Saúde", "2026-10-06", 5_000)

    nomes = [c["nome"] for c in resumo(client)["saidas_por_categoria"]]

    assert nomes == ["Lazer", "Saúde", "Transporte"]


def test_so_salario(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05", 500_000)

    corpo = resumo(client)

    assert (corpo["entradas"], corpo["saidas"], corpo["saldo"]) == (500_000, 0, 500_000)
    assert corpo["saidas_por_categoria"] == []
    assert corpo["ciclo"]["aberto"] is True


def test_ciclo_aberto_inclui_lancamentos_com_data_futura(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", "2026-10-05", 500_000)
    lancar(client, conta, "Moradia", "2027-03-01", 150_000)

    assert resumo(client)["saidas"] == 150_000


def test_categoria_inativa_continua_no_resumo(
    client: TestClient, conta: Conta, ciclo_de_outubro: None, db: Session
) -> None:
    db.execute(
        update(Categoria).where(Categoria.id == conta.categorias["Moradia"]).values(ativa=False)
    )
    db.commit()

    nomes = [c["nome"] for c in resumo(client)["saidas_por_categoria"]]

    assert "Moradia" in nomes


def test_data_sem_ciclo(client: TestClient, conta: Conta, ciclo_de_outubro: None) -> None:
    resposta = client.get("/api/v1/ciclos/2026-10-04/resumo")
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "sem_ciclo"


def test_sem_salario(client: TestClient, conta: Conta) -> None:
    assert client.get("/api/v1/ciclos/2026-10-05/resumo").status_code == 404


def test_resumo_so_do_proprio_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    outro = novo_client()
    bia = criar_conta(outro, email="bia@exemplo.com")
    lancar(outro, bia, "Salário", "2026-10-05", 900_000)
    lancar(outro, bia, "Moradia", "2026-10-06", 400_000)
    lancar(client, conta, "Salário", "2026-10-05", 500_000)

    corpo = resumo(client)

    assert (corpo["entradas"], corpo["saidas"]) == (500_000, 0)


def test_exige_login(client: TestClient) -> None:
    assert client.get("/api/v1/ciclos/2026-10-05/resumo").status_code == 401
