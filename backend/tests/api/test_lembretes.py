"""Feature 015: lembretes (o que vence nos próximos dias)."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/lembretes"
LANCAMENTOS = "/api/v1/lancamentos"


@pytest.fixture(autouse=True)
def hoje_10_de_outubro(relogio: RelogioFixo) -> None:
    # 12h em São Paulo; a janela vai até 13/10.
    relogio.agora = datetime(2026, 10, 10, 15, 0, tzinfo=UTC)


@pytest.fixture
def criar_prestador(db: Session, criar_conta: Callable[..., Conta]) -> Callable[..., Conta]:
    """Prestador: lança previstos sem precisar de salário."""

    def _criar(cliente: TestClient, email: str = "ana@exemplo.com") -> Conta:
        conta = criar_conta(cliente, email)
        conta.usuario.tipo_renda = "prestador"
        db.commit()
        return conta

    return _criar


@pytest.fixture
def conta(client: TestClient, criar_prestador: Callable[..., Conta]) -> Conta:
    return criar_prestador(client)


def lancar(
    client: TestClient,
    conta: Conta,
    data: str,
    categoria: str = "Moradia",
    status: str = "previsto",
    **extra: Any,
) -> dict[str, Any]:
    resposta = client.post(
        LANCAMENTOS,
        json={
            "valor": 150_000,
            "categoria_id": conta.categorias[categoria],
            "data": data,
            "status": status,
            **extra,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def lembretes(client: TestClient) -> dict[str, Any]:
    resposta = client.get(URL)
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def ids(itens: list[dict[str, Any]]) -> list[int]:
    return [item["lancamento"]["id"] for item in itens]


# --- US1: o que vence nos próximos dias --------------------------------------------------------


def test_janela_de_ontem_a_hoje_mais_tres(client: TestClient, conta: Conta) -> None:
    # US1.1, US1.2, US1.3
    ontem = lancar(client, conta, "2026-10-09")
    hoje = lancar(client, conta, "2026-10-10")
    limite = lancar(client, conta, "2026-10-13")
    lancar(client, conta, "2026-10-14")

    corpo = lembretes(client)

    assert corpo["hoje"] == "2026-10-10"
    assert corpo["limite"] == "2026-10-13"
    assert ids(corpo["atrasados"]) == [ontem["id"]]
    assert ids(corpo["a_vencer"]) == [hoje["id"], limite["id"]]


def test_item_de_conta_traz_o_lancamento(client: TestClient, conta: Conta) -> None:
    # US1.1: valor, data, categoria e descrição
    lanc = lancar(client, conta, "2026-10-12", descricao="Aluguel")

    (item,) = lembretes(client)["a_vencer"]

    assert item["origem"] == "conta"
    assert item["situacao"] == "a_vencer"
    assert item["data"] == "2026-10-12"
    assert item["lembrete"] is None
    assert item["lancamento"]["id"] == lanc["id"]
    assert item["lancamento"]["valor"] == 150_000
    assert item["lancamento"]["categoria_id"] == conta.categorias["Moradia"]
    assert item["lancamento"]["descricao"] == "Aluguel"


def test_entrada_prevista_e_valor_a_receber(client: TestClient, conta: Conta) -> None:
    # US1.4
    lancar(client, conta, "2026-10-11", categoria="Renda extra")

    (item,) = lembretes(client)["a_vencer"]

    assert item["origem"] == "valor"
    assert item["lancamento"]["tipo"] == "entrada"


def test_previsto_de_ciclo_anterior_continua_atrasado(client: TestClient, conta: Conta) -> None:
    # Edge case: a janela não depende do ciclo
    antigo = lancar(client, conta, "2026-08-05")

    corpo = lembretes(client)

    assert ids(corpo["atrasados"]) == [antigo["id"]]


def test_parcela_paga_no_cartao_nao_aparece(client: TestClient, conta: Conta) -> None:
    # US1.5: quem é pago é a fatura
    resposta = client.post(
        "/api/v1/dividas",
        json={
            "descricao": "Geladeira",
            "pessoa": "Loja",
            "direcao": "devo",
            "valor_total": 300_000,
            "parcelas": 1,
            "forma_pagamento": "cartao",
            "dia_vencimento": 12,
            "data_inicio": "2026-10-10",
            "categoria_id": conta.categorias["Moradia"],
        },
    )
    assert resposta.status_code == 201, resposta.text
    assert resposta.json()["lancamentos"][0]["conta_no_saldo"] is False

    corpo = lembretes(client)

    assert corpo["atrasados"] == corpo["a_vencer"] == []


def test_confirmado_sai_e_volta_ao_ser_previsto_de_novo(client: TestClient, conta: Conta) -> None:
    # US1.6 e FR-003: derivado na hora
    lanc = lancar(client, conta, "2026-10-10")

    client.patch(f"{LANCAMENTOS}/{lanc['id']}", json={"status": "realizado"})
    assert lembretes(client)["a_vencer"] == []

    client.patch(f"{LANCAMENTOS}/{lanc['id']}", json={"status": "previsto"})
    assert ids(lembretes(client)["a_vencer"]) == [lanc["id"]]


def test_realizado_nao_aparece(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "2026-10-09", status="realizado")

    corpo = lembretes(client)

    assert corpo["atrasados"] == corpo["a_vencer"] == []


def test_ordem_por_data_e_id(client: TestClient, conta: Conta) -> None:
    segundo = lancar(client, conta, "2026-10-12")
    primeiro = lancar(client, conta, "2026-10-11")
    terceiro = lancar(client, conta, "2026-10-12", categoria="Renda extra")

    assert ids(lembretes(client)["a_vencer"]) == [primeiro["id"], segundo["id"], terceiro["id"]]


def test_sem_nada_listas_vazias(client: TestClient, conta: Conta) -> None:
    corpo = lembretes(client)

    assert corpo["atrasados"] == corpo["a_vencer"] == []


def test_exige_sessao(client: TestClient) -> None:
    assert client.get(URL).status_code == 401


def test_nao_ve_lancamentos_de_outro_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_prestador: Callable[..., Conta],
) -> None:
    # US1.7
    outro = novo_client()
    bia = criar_prestador(outro, "bia@exemplo.com")
    lancar(outro, bia, "2026-10-09")
    lancar(outro, bia, "2026-10-11", categoria="Renda extra")
    ana = criar_prestador(client)
    meu = lancar(client, ana, "2026-10-12")

    corpo = lembretes(client)

    assert corpo["atrasados"] == []
    assert ids(corpo["a_vencer"]) == [meu["id"]]
