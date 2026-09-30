"""Feature 012: prestador de serviço, com ciclo pelo mês do calendário."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import Conta, RelogioFixo

CICLOS = "/api/v1/ciclos"
LANCAMENTOS = "/api/v1/lancamentos"


@pytest.fixture(autouse=True)
def hoje_15_de_outubro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 10, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def criar_prestador(db: Session, criar_conta: Callable[..., Conta]) -> Callable[..., Conta]:
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
    client: TestClient, conta: Conta, categoria: str, data: str, valor: int = 10_000, **extra: Any
) -> dict[str, Any]:
    resposta = client.post(
        LANCAMENTOS,
        json={"valor": valor, "categoria_id": conta.categorias[categoria], "data": data, **extra},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def recorrencia(
    client: TestClient, conta: Conta, dia: int, categoria: str = "Moradia", valor: int = 120_000
) -> dict[str, Any]:
    resposta = client.post(
        "/api/v1/recorrencias",
        json={
            "descricao": "Aluguel",
            "valor": valor,
            "categoria_id": conta.categorias[categoria],
            "dia": dia,
        },
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def previstos(client: TestClient, data: str) -> list[dict[str, Any]]:
    resposta = client.get(f"{CICLOS}/{data}/lancamentos")
    assert resposta.status_code == 200, resposta.text
    return [lanc for lanc in resposta.json() if lanc["recorrencia_id"] is not None]


# --- US2: controlar o mês sem salário ------------------------------------------------------


def test_lanca_gasto_sem_salario(client: TestClient, conta: Conta) -> None:
    # US2.1
    lancamento = lancar(client, conta, "Alimentação", "2026-10-15", 5_000)

    assert lancamento["abre_ciclo"] is False


def test_ciclo_atual_e_o_mes_de_hoje(client: TestClient, conta: Conta) -> None:
    # US2.2 e US2.3: sem lançamentos, o ciclo atual existe
    resposta = client.get(f"{CICLOS}/atual")

    assert resposta.status_code == 200
    assert resposta.json() == {
        "inicio": "2026-10-01",
        "fim": "2026-10-31",
        "aberto": True,
        "anterior": None,
        "proximo": None,
    }


def test_resumo_do_mes(client: TestClient, conta: Conta) -> None:
    # US2.4
    lancar(client, conta, "Renda extra", "2026-10-03", 200_000)
    lancar(client, conta, "Alimentação", "2026-10-20", 50_000)
    lancar(client, conta, "Alimentação", "2026-09-30", 7_000)  # outro mês
    lancar(client, conta, "Renda extra", "2026-11-01", 9_000)  # outro mês

    resumo = client.get(f"{CICLOS}/2026-10-15/resumo").json()

    assert (resumo["entradas"], resumo["saidas"], resumo["saldo"]) == (200_000, 50_000, 150_000)
    assert resumo["ciclo"]["inicio"] == "2026-10-01"
    assert resumo["ciclo"]["fim"] == "2026-10-31"


def test_fevereiro_bissexto(client: TestClient, conta: Conta) -> None:
    # US2.5
    ciclo = client.get(f"{CICLOS}/2028-02-10").json()

    assert (ciclo["inicio"], ciclo["fim"], ciclo["aberto"]) == ("2028-02-01", "2028-02-29", False)


def test_salario_e_entrada_comum(client: TestClient, conta: Conta) -> None:
    # US2.6 e US2.7
    realizado = lancar(client, conta, "Salário", "2026-10-10", 300_000)
    previsto = lancar(client, conta, "Salário", "2026-11-05", 300_000, status="previsto")

    assert realizado["abre_ciclo"] is False
    assert previsto["status"] == "previsto"
    assert client.get(f"{CICLOS}/atual").json()["inicio"] == "2026-10-01"
    resumo = client.get(f"{CICLOS}/2026-10-15/resumo").json()
    assert resumo["entradas"] == 300_000


def test_salario_pode_mudar_para_previsto_e_data_futura(client: TestClient, conta: Conta) -> None:
    salario = lancar(client, conta, "Salário", "2026-10-10", 300_000)

    resposta = client.patch(
        f"{LANCAMENTOS}/{salario['id']}", json={"status": "previsto", "data": "2026-12-01"}
    )

    assert resposta.status_code == 200, resposta.text


def test_excluir_unico_salario_nao_deixa_nada_fora_de_ciclo(
    client: TestClient, conta: Conta
) -> None:
    salario = lancar(client, conta, "Salário", "2026-10-10", 300_000)
    lancar(client, conta, "Alimentação", "2026-10-12")

    assert client.delete(f"{LANCAMENTOS}/{salario['id']}").status_code == 204


def test_vizinhos_do_mes(client: TestClient, conta: Conta) -> None:
    # US2.8
    lancar(client, conta, "Alimentação", "2026-08-20")

    outubro = client.get(f"{CICLOS}/atual").json()
    assert (outubro["anterior"], outubro["proximo"]) == ("2026-09-01", None)
    setembro = client.get(f"{CICLOS}/2026-09-10").json()
    assert (setembro["anterior"], setembro["proximo"]) == ("2026-08-01", "2026-10-01")
    agosto = client.get(f"{CICLOS}/2026-08-10").json()
    assert (agosto["anterior"], agosto["proximo"]) == (None, "2026-09-01")


def test_mes_futuro_fechado_sem_proximo(client: TestClient, conta: Conta) -> None:
    ciclo = client.get(f"{CICLOS}/2026-12-05").json()

    assert (ciclo["inicio"], ciclo["aberto"], ciclo["proximo"]) == ("2026-12-01", False, None)


def test_divida_sem_salario(client: TestClient, conta: Conta) -> None:
    resposta = client.post(
        "/api/v1/dividas",
        json={
            "descricao": "Notebook",
            "pessoa": "Loja X",
            "direcao": "devo",
            "valor_total": 100_000,
            "parcelas": 3,
            "forma_pagamento": "pix",
            "dia_vencimento": 15,
            "data_inicio": "2026-10-05",
            "categoria_id": conta.categorias["Outros"],
        },
    )

    assert resposta.status_code == 201, resposta.text


def test_deposito_na_cartela_sem_salario(client: TestClient, conta: Conta) -> None:
    cartela = client.post("/api/v1/cartelas", json={"nome": "Viagem", "meta": 1_000}).json()
    casa = cartela["casas"][0]

    resposta = client.post(f"/api/v1/cartelas/{cartela['id']}/casas/{casa['id']}/deposito")

    assert resposta.status_code == 200, resposta.text


def test_importacao_sem_salario(client: TestClient, conta: Conta) -> None:
    from tests.api.test_importacao import arquivo, confirmacao

    resposta = client.post(
        "/api/v1/importacoes/previa",
        json={"banco": "inter", "formato": "ofx", "arquivo_base64": arquivo("inter.ofx")},
    )
    linhas = resposta.json()["linhas"]
    assert [linha["situacao"] for linha in linhas] == ["nova", "nova", "nova"]

    c = conta.categorias
    # A entrada vai para "Salário": para o prestador, não abre ciclo.
    categorias = [c["Salário"], c["Alimentação"], c["Moradia"]]
    resposta = client.post("/api/v1/importacoes", json=confirmacao(linhas, categorias))

    assert resposta.status_code == 201, resposta.text
    assert client.get(f"{CICLOS}/atual").json()["inicio"] == "2026-10-01"


def test_importacao_aceita_salario_com_data_futura(client: TestClient, conta: Conta) -> None:
    corpo = {
        "linhas": [
            {
                "id_externo": "inter:ofx:futuro",
                "data": "2026-11-05",
                "valor": 300_000,
                "tipo": "entrada",
                "descricao": "Cliente",
                "categoria_id": conta.categorias["Salário"],
            }
        ]
    }

    assert client.post("/api/v1/importacoes", json=corpo).status_code == 201


def test_clt_continua_exigindo_salario(
    client: TestClient,
    conta: Conta,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
) -> None:
    lancar(client, conta, "Alimentação", "2026-10-15")
    outro = novo_client()
    bia = criar_conta(outro, "bia@exemplo.com")

    resposta = outro.post(
        LANCAMENTOS,
        json={"valor": 1_000, "categoria_id": bia.categorias["Alimentação"], "data": "2026-10-15"},
    )

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "salario_necessario"
    assert outro.get(f"{CICLOS}/atual").status_code == 404


# --- US3: fixos e limites no mês -----------------------------------------------------------


def test_recorrencia_gera_previsto_no_mes(client: TestClient, conta: Conta) -> None:
    # US3.1
    aluguel = recorrencia(client, conta, dia=10)

    gerados = previstos(client, "2026-10-15")
    assert [(g["data"], g["valor"], g["recorrencia_id"]) for g in gerados] == [
        ("2026-10-10", 120_000, aluguel["id"])
    ]


def test_mes_novo_gera_o_previsto_ao_consultar(
    client: TestClient, conta: Conta, relogio: RelogioFixo
) -> None:
    # US3.2
    recorrencia(client, conta, dia=10)
    relogio.agora = datetime(2026, 11, 3, 15, 0, tzinfo=UTC)

    assert previstos(client, "2026-11-03") == []
    assert client.get(f"{CICLOS}/atual").status_code == 200
    assert [g["data"] for g in previstos(client, "2026-11-03")] == ["2026-11-10"]


def test_resumo_tambem_gera_o_previsto(
    client: TestClient, conta: Conta, relogio: RelogioFixo
) -> None:
    recorrencia(client, conta, dia=10)
    relogio.agora = datetime(2026, 11, 3, 15, 0, tzinfo=UTC)

    client.get(f"{CICLOS}/2026-11-03/resumo")

    assert [g["data"] for g in previstos(client, "2026-11-03")] == ["2026-11-10"]


def test_lancar_no_mes_novo_gera_o_previsto(
    client: TestClient, conta: Conta, relogio: RelogioFixo
) -> None:
    recorrencia(client, conta, dia=10)
    relogio.agora = datetime(2026, 11, 3, 15, 0, tzinfo=UTC)

    lancar(client, conta, "Alimentação", "2026-11-03")

    assert [g["data"] for g in previstos(client, "2026-11-03")] == ["2026-11-10"]


def test_consultar_varias_vezes_nao_duplica(client: TestClient, conta: Conta) -> None:
    # US3.3
    recorrencia(client, conta, dia=10)

    for _ in range(3):
        client.get(f"{CICLOS}/atual")
        client.get(f"{CICLOS}/2026-10-15/resumo")

    assert len(previstos(client, "2026-10-15")) == 1


def test_dia_31_em_fevereiro(
    client: TestClient, criar_prestador: Callable[..., Conta], relogio: RelogioFixo
) -> None:
    # US3.4
    relogio.agora = datetime(2027, 1, 20, 15, 0, tzinfo=UTC)
    conta = criar_prestador(client)
    recorrencia(client, conta, dia=31)
    relogio.agora = datetime(2027, 2, 5, 15, 0, tzinfo=UTC)

    client.get(f"{CICLOS}/atual")

    assert [g["data"] for g in previstos(client, "2027-02-05")] == ["2027-02-28"]


def test_limite_medido_no_mes(client: TestClient, conta: Conta) -> None:
    # US3.5
    client.patch(f"/api/v1/categorias/{conta.categorias['Lazer']}", json={"limite": 30_000})
    lancar(client, conta, "Lazer", "2026-09-20", 20_000)

    # Em outubro só conta o gasto de outubro: R$ 200 + R$ 100 em setembro seria "atenção".
    outubro = lancar(client, conta, "Lazer", "2026-10-01", 10_000)
    assert outubro["aviso_limite"] is None

    setembro = lancar(client, conta, "Lazer", "2026-09-25", 5_000)
    assert setembro["aviso_limite"]["situacao"] == "atencao"
    assert setembro["aviso_limite"]["usado"] == 25_000


# --- US4: trocar o tipo de renda -----------------------------------------------------------


def trocar(client: TestClient, tipo: str) -> Any:
    return client.patch("/api/v1/me", json={"tipo_renda": tipo})


def test_clt_vira_prestador(client: TestClient, criar_conta: Callable[..., Conta]) -> None:
    # US4.1
    clt = criar_conta(client)
    lancar(client, clt, "Salário", "2026-10-05", 500_000)
    lancar(client, clt, "Alimentação", "2026-10-06")
    assert client.get(f"{CICLOS}/atual").json()["inicio"] == "2026-10-05"

    resposta = trocar(client, "prestador")

    assert resposta.status_code == 200
    assert resposta.json()["tipo_renda"] == "prestador"
    assert client.get(f"{CICLOS}/atual").json()["inicio"] == "2026-10-01"
    lancamentos = client.get(f"{CICLOS}/2026-10-15/lancamentos").json()
    assert len(lancamentos) == 2
    assert all(lanc["abre_ciclo"] is False for lanc in lancamentos)


@pytest.mark.parametrize("novo", ["clt", "clt_prestador"])
def test_prestador_sem_salario_nao_vira_clt(client: TestClient, conta: Conta, novo: str) -> None:
    # US4.2
    lancar(client, conta, "Alimentação", "2026-10-06")

    resposta = trocar(client, novo)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamentos_sem_ciclo"
    assert client.get("/api/v1/me").json()["tipo_renda"] == "prestador"


def test_lancamento_antes_do_primeiro_salario(client: TestClient, conta: Conta) -> None:
    # US4.3
    lancar(client, conta, "Salário", "2026-09-05", 500_000)
    lancar(client, conta, "Alimentação", "2026-09-02")

    resposta = trocar(client, "clt")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamentos_sem_ciclo"


def test_prestador_com_salario_cobrindo_tudo_vira_clt(client: TestClient, conta: Conta) -> None:
    # US4.4
    lancar(client, conta, "Salário", "2026-09-05", 500_000)
    lancar(client, conta, "Alimentação", "2026-09-05")
    lancar(client, conta, "Alimentação", "2026-10-10")

    resposta = trocar(client, "clt")

    assert resposta.status_code == 200
    assert client.get(f"{CICLOS}/atual").json() == {
        "inicio": "2026-09-05",
        "fim": None,
        "aberto": True,
        "anterior": None,
        "proximo": None,
    }


def test_prestador_sem_lancamentos_vira_clt(client: TestClient, conta: Conta) -> None:
    # US4.5
    assert trocar(client, "clt").status_code == 200


@pytest.mark.parametrize(
    ("data", "extra"), [("2026-10-05", {"status": "previsto"}), ("2026-10-20", {})]
)
def test_salario_previsto_ou_futuro_impede_virar_clt(
    client: TestClient, conta: Conta, data: str, extra: dict[str, Any]
) -> None:
    # US4.6
    lancar(client, conta, "Salário", "2026-10-01", 500_000)
    lancar(client, conta, "Salário", data, 500_000, **extra)

    resposta = trocar(client, "clt")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "salario_invalido"


def test_clt_prestador_vira_clt(client: TestClient, criar_conta: Callable[..., Conta]) -> None:
    criar_conta(client)
    assert trocar(client, "clt_prestador").status_code == 200
    assert trocar(client, "clt").status_code == 200
