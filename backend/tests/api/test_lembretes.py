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


# --- US4: lembretes livres ---------------------------------------------------------------------

LIVRES = f"{URL}/livres"


def criar_livre(
    client: TestClient, texto: str = "Renovar o seguro", data: str = "2026-10-12"
) -> dict[str, Any]:
    resposta = client.post(LIVRES, json={"texto": texto, "data": data})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_cria_lembrete_livre(client: TestClient, conta: Conta) -> None:
    # US4.1
    resposta = client.post(LIVRES, json={"texto": "  Renovar o seguro  ", "data": "2026-10-12"})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo == {
        "id": corpo["id"],
        "texto": "Renovar o seguro",
        "data": "2026-10-12",
        "concluido": False,
        "concluido_em": None,
        "criado_em": corpo["criado_em"],
    }


@pytest.mark.parametrize(
    ("corpo", "campo"),
    [
        ({"texto": "", "data": "2026-10-12"}, "texto"),
        ({"texto": "   ", "data": "2026-10-12"}, "texto"),
        ({"texto": "x" * 201, "data": "2026-10-12"}, "texto"),
        ({"texto": "Seguro"}, "data"),
        ({"texto": "Seguro", "data": "amanhã"}, "data"),
    ],
)
def test_validacao_do_lembrete_livre(
    client: TestClient, conta: Conta, corpo: dict[str, Any], campo: str
) -> None:
    # US4.6
    resposta = client.post(LIVRES, json=corpo)

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_texto_com_200_caracteres_e_campo_extra(client: TestClient, conta: Conta) -> None:
    assert client.post(LIVRES, json={"texto": "x" * 200, "data": "2026-10-12"}).status_code == 201
    extra = client.post(LIVRES, json={"texto": "Seguro", "data": "2026-10-12", "valor": 1})
    assert extra.status_code == 422


def test_lista_todos_por_data_inclusive_concluidos_e_futuros(
    client: TestClient, conta: Conta
) -> None:
    futuro = criar_livre(client, "Vistoria", "2026-11-20")
    passado = criar_livre(client, "Pagar IPVA", "2026-09-01")
    concluido = criar_livre(client, "Ligar para o banco", "2026-10-11")
    client.patch(f"{LIVRES}/{concluido['id']}", json={"concluido": True})

    corpo = client.get(LIVRES).json()

    assert [item["id"] for item in corpo] == [passado["id"], concluido["id"], futuro["id"]]
    assert [item["concluido"] for item in corpo] == [False, True, False]


def test_edita_texto_e_data(client: TestClient, conta: Conta) -> None:
    # US4.5
    livre = criar_livre(client)

    resposta = client.patch(
        f"{LIVRES}/{livre['id']}", json={"texto": "Seguro do carro", "data": "2026-10-13"}
    )

    assert resposta.status_code == 200
    assert (resposta.json()["texto"], resposta.json()["data"]) == ("Seguro do carro", "2026-10-13")


def test_concluir_e_desfazer(client: TestClient, conta: Conta) -> None:
    # US4.4
    livre = criar_livre(client)

    concluido = client.patch(f"{LIVRES}/{livre['id']}", json={"concluido": True}).json()
    assert concluido["concluido"] is True
    assert concluido["concluido_em"] == "2026-10-10T15:00:00Z"
    assert lembretes(client)["a_vencer"] == []

    reaberto = client.patch(f"{LIVRES}/{livre['id']}", json={"concluido": False}).json()
    assert reaberto["concluido"] is False
    assert reaberto["concluido_em"] is None


@pytest.mark.parametrize("campo", ["texto", "data", "concluido"])
def test_patch_recusa_null(client: TestClient, conta: Conta, campo: str) -> None:
    livre = criar_livre(client)

    resposta = client.patch(f"{LIVRES}/{livre['id']}", json={campo: None})

    assert resposta.status_code == 422


def test_exclui(client: TestClient, conta: Conta) -> None:
    livre = criar_livre(client)

    assert client.delete(f"{LIVRES}/{livre['id']}").status_code == 204
    assert client.get(LIVRES).json() == []


def test_livre_entra_na_janela_como_os_lancamentos(client: TestClient, conta: Conta) -> None:
    # US4.1, US4.2, US4.3, FR-006
    atrasado = criar_livre(client, "Pagar IPVA", "2026-10-08")
    a_vencer = criar_livre(client, "Renovar o seguro", "2026-10-13")
    criar_livre(client, "Vistoria", "2026-10-14")
    lanc = lancar(client, conta, "2026-10-13")

    corpo = lembretes(client)

    (item_atrasado,) = corpo["atrasados"]
    assert item_atrasado["origem"] == "livre"
    assert item_atrasado["lancamento"] is None
    assert item_atrasado["lembrete"]["id"] == atrasado["id"]
    assert [(i["origem"], (i["lancamento"] or i["lembrete"])["id"]) for i in corpo["a_vencer"]] == [
        ("conta", lanc["id"]),
        ("livre", a_vencer["id"]),
    ]


def test_lembrete_livre_de_outro_usuario_nao_e_encontrado(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_prestador: Callable[..., Conta],
) -> None:
    # US4.7
    outro = novo_client()
    criar_prestador(outro, "bia@exemplo.com")
    da_bia = criar_livre(outro, "Segredo da Bia", "2026-10-11")
    criar_prestador(client)

    assert client.patch(f"{LIVRES}/{da_bia['id']}", json={"concluido": True}).status_code == 404
    resposta = client.delete(f"{LIVRES}/{da_bia['id']}")
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "nao_encontrado"
    assert client.get(LIVRES).json() == []
    assert lembretes(client)["a_vencer"] == []
