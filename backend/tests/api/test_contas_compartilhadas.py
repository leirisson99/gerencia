from collections.abc import Callable
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from tests.conftest import Conta

URL = "/api/v1/contas-compartilhadas"


@pytest.fixture
def ana(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


def criar(client: TestClient, conta: Conta, **alteracoes: Any) -> httpx.Response:
    dados: dict[str, Any] = {
        "descricao": "Energia",
        "categoria_id": conta.categorias["Outros"],
        "modo": "igual",
        "dia_vencimento": 10,
    }
    dados.update(alteracoes)
    return client.post(URL, json=dados)


def convidar(client: TestClient, conta_id: int, email: str, **extra: Any) -> httpx.Response:
    return client.post(f"{URL}/{conta_id}/participantes", json={"email": email, **extra})


# --- US1: cadastrar a conta e dividir -------------------------------------------------------


def test_cria_a_conta_com_o_dono_como_participante_aceito(client: TestClient, ana: Conta) -> None:
    resposta = criar(client, ana)

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["papel"] == "dono"
    assert corpo["descricao"] == "Energia"
    assert corpo["ativa"] is True
    assert corpo["qtd_pessoas"] == 1
    assert corpo["qtd_convidados_pendentes"] == 0
    assert corpo["valor_total"] is None
    assert corpo["falta_informar_total"] is True  # conta variável, sem total do mês
    [dono] = corpo["participantes"]
    assert dono["eh_dono"] is True
    assert dono["status"] == "aceito"


def test_conta_com_valor_fixo_nao_pede_total(client: TestClient, ana: Conta) -> None:
    corpo = criar(client, ana, descricao="Aluguel", valor_fixo=200_000).json()

    assert corpo["valor_fixo"] == 200_000
    assert corpo["falta_informar_total"] is False


@pytest.mark.parametrize(
    "alteracao",
    [
        {"modo": "outro"},
        {"dia_vencimento": 0},
        {"dia_vencimento": 32},
        {"valor_fixo": 0},
        {"valor_fixo": -1},
        {"descricao": "   "},
        {"descricao": "x" * 201},
    ],
)
def test_dados_invalidos_da_conta(
    client: TestClient, ana: Conta, alteracao: dict[str, Any]
) -> None:
    assert criar(client, ana, **alteracao).status_code == 422


def test_categoria_de_entrada_e_recusada(client: TestClient, ana: Conta) -> None:
    resposta = criar(client, ana, categoria_id=ana.categorias["Salário"])

    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["erro"]["campos"]


def test_categoria_de_outro_usuario_nao_existe(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    ana: Conta,
) -> None:
    bia = criar_conta(novo_client(), email="bia@exemplo.com")

    resposta = criar(client, ana, categoria_id=bia.categorias["Outros"])

    assert resposta.status_code == 404


def test_convidados_pendentes_nao_entram_na_quantidade_de_pessoas(
    client: TestClient, ana: Conta
) -> None:
    conta_id = criar(client, ana).json()["id"]
    convidar(client, conta_id, "bia@exemplo.com")
    convidar(client, conta_id, "caio@exemplo.com")

    corpo = client.get(f"{URL}/{conta_id}").json()

    assert corpo["qtd_pessoas"] == 1
    assert corpo["qtd_convidados_pendentes"] == 2
    emails = {p["email_convite"] for p in corpo["participantes"] if not p["eh_dono"]}
    assert emails == {"bia@exemplo.com", "caio@exemplo.com"}


def test_convite_responde_igual_exista_conta_ou_nao(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    ana: Conta,
) -> None:
    criar_conta(novo_client(), email="existe@exemplo.com")
    conta_id = criar(client, ana).json()["id"]

    com_conta = convidar(client, conta_id, "existe@exemplo.com")
    sem_conta = convidar(client, conta_id, "ninguem@exemplo.com")

    assert com_conta.status_code == sem_conta.status_code == 201

    def sem_ids(resposta: httpx.Response) -> list[dict[str, Any]]:
        return [
            {k: v for k, v in p.items() if k not in ("id", "email_convite")}
            for p in resposta.json()["participantes"]
            if not p["eh_dono"]
        ]

    # O dono não descobre quem já tem conta: nada de nome ou vínculo antes do aceite.
    assert sem_ids(com_conta)[0] == sem_ids(sem_conta)[0]


def test_email_e_normalizado_e_convite_repetido_nao_duplica(client: TestClient, ana: Conta) -> None:
    conta_id = criar(client, ana).json()["id"]

    convidar(client, conta_id, "Bia@Exemplo.com ")
    resposta = convidar(client, conta_id, "bia@exemplo.com")

    assert resposta.status_code == 201
    convidados = [p for p in resposta.json()["participantes"] if not p["eh_dono"]]
    assert [c["email_convite"] for c in convidados] == ["bia@exemplo.com"]


def test_convidar_o_proprio_dono_nao_cria_participante(client: TestClient, ana: Conta) -> None:
    conta_id = criar(client, ana).json()["id"]

    resposta = convidar(client, conta_id, ana.usuario.email)

    assert resposta.status_code == 201
    assert len(resposta.json()["participantes"]) == 1


def test_email_invalido_no_convite(client: TestClient, ana: Conta) -> None:
    conta_id = criar(client, ana).json()["id"]

    assert convidar(client, conta_id, "isso-nao-e-email").status_code == 422


def test_limite_de_vinte_participantes_com_o_dono(client: TestClient, ana: Conta) -> None:
    conta_id = criar(client, ana).json()["id"]
    for n in range(19):
        assert convidar(client, conta_id, f"pessoa{n}@exemplo.com").status_code == 201

    resposta = convidar(client, conta_id, "vigesimo-primeiro@exemplo.com")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "limite_participantes"


def test_dono_edita_a_conta(client: TestClient, ana: Conta) -> None:
    conta_id = criar(client, ana, valor_fixo=100_000).json()["id"]

    corpo = client.patch(
        f"{URL}/{conta_id}", json={"descricao": "Energia elétrica", "valor_fixo": None}
    ).json()

    assert corpo["descricao"] == "Energia elétrica"
    assert corpo["valor_fixo"] is None
    assert corpo["dia_vencimento"] == 10


def test_dono_desativa_a_conta(client: TestClient, ana: Conta) -> None:
    conta_id = criar(client, ana).json()["id"]

    assert client.patch(f"{URL}/{conta_id}", json={"ativa": False}).json()["ativa"] is False


def test_dono_define_o_valor_de_cada_participante_inclusive_o_dele(
    client: TestClient, ana: Conta
) -> None:
    conta_id = criar(client, ana, modo="percentual").json()["id"]
    corpo = convidar(client, conta_id, "bia@exemplo.com", valor=3_000).json()
    dono, bia = sorted(corpo["participantes"], key=lambda p: not p["eh_dono"])

    resposta = client.patch(f"{URL}/{conta_id}/participantes/{dono['id']}", json={"valor": 7_000})

    assert resposta.status_code == 200
    valores = {p["email_convite"]: p["valor"] for p in resposta.json()["participantes"]}
    assert valores == {None: 7_000, "bia@exemplo.com": 3_000}
    assert bia["valor"] == 3_000


def test_remove_um_convidado_mas_nao_o_dono(client: TestClient, ana: Conta) -> None:
    conta_id = criar(client, ana).json()["id"]
    corpo = convidar(client, conta_id, "bia@exemplo.com").json()
    dono = next(p for p in corpo["participantes"] if p["eh_dono"])
    bia = next(p for p in corpo["participantes"] if not p["eh_dono"])

    assert client.delete(f"{URL}/{conta_id}/participantes/{bia['id']}").status_code == 200
    recusada = client.delete(f"{URL}/{conta_id}/participantes/{dono['id']}")

    assert recusada.status_code == 409
    restantes = client.get(f"{URL}/{conta_id}").json()["participantes"]
    assert {p["status"] for p in restantes if not p["eh_dono"]} == {"removido"}
    assert client.get(f"{URL}/{conta_id}").json()["qtd_convidados_pendentes"] == 0


def test_lista_as_contas_do_dono(client: TestClient, ana: Conta) -> None:
    criar(client, ana, descricao="Aluguel", valor_fixo=200_000)
    criar(client, ana, descricao="Água")

    corpo = client.get(URL).json()

    assert {c["descricao"] for c in corpo} == {"Aluguel", "Água"}
    assert all(c["papel"] == "dono" for c in corpo)


def test_quem_nao_participa_recebe_404(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    ana: Conta,
) -> None:
    conta_id = criar(client, ana).json()["id"]
    caio = novo_client()
    criar_conta(caio, email="caio@exemplo.com")

    assert caio.get(f"{URL}/{conta_id}").status_code == 404
    assert caio.patch(f"{URL}/{conta_id}", json={"descricao": "x"}).status_code == 404
    assert convidar(caio, conta_id, "z@exemplo.com").status_code == 404
    assert caio.get(URL).json() == []
