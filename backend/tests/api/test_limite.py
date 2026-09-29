from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from fastapi.testclient import TestClient

from tests.conftest import Conta, RelogioFixo

CATEGORIAS = "/api/v1/categorias"
LANCAMENTOS = "/api/v1/lancamentos"
LIMITE = 30_000  # R$ 300,00


@pytest.fixture(autouse=True)
def hoje_15_de_janeiro_de_2027(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2027, 1, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


@pytest.fixture
def salario(client: TestClient, conta: Conta) -> None:
    lancar(client, conta, "Salário", 500_000, "2027-01-05")


@pytest.fixture
def lazer_com_limite(client: TestClient, conta: Conta) -> None:
    definir_limite(client, conta, "Lazer", LIMITE)


def definir_limite(client: TestClient, conta: Conta, nome: str, limite: int | None) -> Any:
    resposta = client.patch(f"{CATEGORIAS}/{conta.categorias[nome]}", json={"limite": limite})
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def lancar(
    client: TestClient,
    conta: Conta,
    categoria: str,
    valor: int,
    data: str = "2027-01-10",
    **extra: Any,
) -> dict[str, Any]:
    resposta = client.post(
        LANCAMENTOS,
        json={"valor": valor, "categoria_id": conta.categorias[categoria], "data": data, **extra},
    )
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def item_do_resumo(client: TestClient, conta: Conta, nome: str, data: str = "2027-01-10") -> Any:
    corpo = client.get(f"/api/v1/ciclos/{data}/resumo").json()
    return next(
        (i for i in corpo["saidas_por_categoria"] if i["categoria_id"] == conta.categorias[nome]),
        None,
    )


# --- US1: definir o limite -----------------------------------------------------------------


def test_define_muda_e_remove_o_limite(client: TestClient, conta: Conta) -> None:
    assert definir_limite(client, conta, "Lazer", 30_000)["limite"] == 30_000
    assert definir_limite(client, conta, "Lazer", 40_000)["limite"] == 40_000

    lazer = next(c for c in client.get(CATEGORIAS).json() if c["nome"] == "Lazer")
    assert lazer["limite"] == 40_000

    assert definir_limite(client, conta, "Lazer", None)["limite"] is None


def test_patch_sem_limite_nao_mexe_no_limite(client: TestClient, conta: Conta) -> None:
    definir_limite(client, conta, "Lazer", 30_000)

    corpo = client.patch(f"{CATEGORIAS}/{conta.categorias['Lazer']}", json={"nome": "Diversão"})

    assert corpo.json()["limite"] == 30_000


def test_cria_categoria_ja_com_limite(client: TestClient, conta: Conta) -> None:
    resposta = client.post(CATEGORIAS, json={"nome": "Pets", "tipo": "saida", "limite": 20_000})

    assert resposta.status_code == 201
    assert resposta.json()["limite"] == 20_000


def test_categoria_sem_limite_mostra_null(client: TestClient, conta: Conta) -> None:
    assert all(c["limite"] is None for c in client.get(CATEGORIAS).json())


def test_limite_em_categoria_de_entrada_e_recusado(client: TestClient, conta: Conta) -> None:
    editar = client.patch(
        f"{CATEGORIAS}/{conta.categorias['Renda extra']}", json={"limite": 10_000}
    )
    criar = client.post(CATEGORIAS, json={"nome": "Bicos", "tipo": "entrada", "limite": 10_000})

    for resposta in (editar, criar):
        assert resposta.status_code == 422
        assert "limite" in resposta.json()["erro"]["campos"]


@pytest.mark.parametrize("limite", [0, -100, 10.5, "300"])
def test_limite_invalido(client: TestClient, conta: Conta, limite: Any) -> None:
    resposta = client.patch(f"{CATEGORIAS}/{conta.categorias['Lazer']}", json={"limite": limite})

    assert resposta.status_code == 422
    assert "limite" in resposta.json()["erro"]["campos"]


def test_poupanca_do_sistema_aceita_limite(client: TestClient, conta: Conta) -> None:
    assert definir_limite(client, conta, "Poupança", 50_000)["limite"] == 50_000


def test_limite_de_categoria_de_outro_usuario(
    client: TestClient, conta: Conta, criar_conta: Callable[..., Conta]
) -> None:
    outra = criar_conta(client, email="bia@exemplo.com")  # cliente passa a ser a Bia
    resposta = client.patch(f"{CATEGORIAS}/{conta.categorias['Lazer']}", json={"limite": 1_000})

    assert outra.usuario.id != conta.usuario.id
    assert resposta.status_code == 404


# --- US2: uso do limite no resumo ----------------------------------------------------------


@pytest.mark.parametrize(
    ("gastos", "total", "situacao"),
    [
        ([10_000], 10_000, "ok"),
        ([24_000], 24_000, "atencao"),  # 80% exatos
        ([30_000], 30_000, "atencao"),  # 100% exatos
        ([30_001], 30_001, "estourado"),
    ],
)
def test_situacao_no_resumo(
    client: TestClient,
    conta: Conta,
    salario: None,
    lazer_com_limite: None,
    gastos: list[int],
    total: int,
    situacao: str,
) -> None:
    for valor in gastos:
        lancar(client, conta, "Lazer", valor)

    assert item_do_resumo(client, conta, "Lazer") == {
        "categoria_id": conta.categorias["Lazer"],
        "nome": "Lazer",
        "total": total,
        "limite": LIMITE,
        "situacao": situacao,
    }


def test_categoria_com_limite_sem_gasto_aparece_zerada(
    client: TestClient, conta: Conta, salario: None, lazer_com_limite: None
) -> None:
    lancar(client, conta, "Moradia", 100_000)

    corpo = client.get("/api/v1/ciclos/2027-01-10/resumo").json()

    nomes = [i["nome"] for i in corpo["saidas_por_categoria"]]
    assert nomes == ["Moradia", "Lazer"]  # com gasto primeiro
    assert corpo["saidas_por_categoria"][1]["total"] == 0
    assert corpo["saidas_por_categoria"][1]["situacao"] == "ok"
    assert sum(i["total"] for i in corpo["saidas_por_categoria"]) == corpo["saidas"]


def test_previsto_nao_conta_no_limite(
    client: TestClient, conta: Conta, salario: None, lazer_com_limite: None
) -> None:
    lancar(client, conta, "Lazer", 50_000, status="previsto")

    item = item_do_resumo(client, conta, "Lazer")
    assert (item["total"], item["situacao"]) == (0, "ok")


def test_sem_limite_nao_tem_situacao(client: TestClient, conta: Conta, salario: None) -> None:
    lancar(client, conta, "Moradia", 100_000)

    item = item_do_resumo(client, conta, "Moradia")
    assert (item["limite"], item["situacao"]) == (None, None)
    corpo = client.get("/api/v1/ciclos/2027-01-10/resumo").json()
    assert all(
        i["limite"] is None and i["situacao"] is None for i in corpo["entradas_por_categoria"]
    )


def test_categoria_desativada_com_limite_e_sem_gasto_nao_aparece(
    client: TestClient, conta: Conta, salario: None, lazer_com_limite: None
) -> None:
    client.patch(f"{CATEGORIAS}/{conta.categorias['Lazer']}", json={"ativa": False})

    assert item_do_resumo(client, conta, "Lazer") is None


def test_mudar_o_limite_vale_para_ciclos_passados(
    client: TestClient, conta: Conta, salario: None, lazer_com_limite: None
) -> None:
    lancar(client, conta, "Lazer", 25_000)
    lancar(client, conta, "Salário", 500_000, "2027-01-12")  # fecha o ciclo anterior

    definir_limite(client, conta, "Lazer", 20_000)

    assert item_do_resumo(client, conta, "Lazer")["situacao"] == "estourado"


# --- US3: aviso ao lançar ------------------------------------------------------------------


@pytest.fixture
def lazer_com_200(client: TestClient, conta: Conta, salario: None, lazer_com_limite: None) -> None:
    lancar(client, conta, "Lazer", 20_000)


def test_aviso_de_atencao_e_de_estouro_uma_vez_cada(
    client: TestClient, conta: Conta, lazer_com_200: None
) -> None:
    atencao = lancar(client, conta, "Lazer", 5_000)["aviso_limite"]
    assert atencao == {
        "categoria_id": conta.categorias["Lazer"],
        "nome": "Lazer",
        "usado": 25_000,
        "limite": LIMITE,
        "situacao": "atencao",
    }
    assert lancar(client, conta, "Lazer", 1_000)["aviso_limite"] is None  # não piorou
    estouro = lancar(client, conta, "Lazer", 5_000)["aviso_limite"]
    assert (estouro["situacao"], estouro["usado"]) == ("estourado", 31_000)


def test_sem_aviso_quando_continua_ok(
    client: TestClient, conta: Conta, lazer_com_200: None
) -> None:
    assert lancar(client, conta, "Lazer", 1_000)["aviso_limite"] is None


def test_previsto_nao_avisa_e_confirmar_avisa(
    client: TestClient, conta: Conta, lazer_com_200: None
) -> None:
    previsto = lancar(client, conta, "Lazer", 10_000, status="previsto")
    assert previsto["aviso_limite"] is None

    confirmado = client.patch(f"{LANCAMENTOS}/{previsto['id']}", json={"status": "realizado"})

    assert confirmado.status_code == 200
    # 200 + 100 = 300: exatamente 100% ainda é atenção.
    assert confirmado.json()["aviso_limite"]["situacao"] == "atencao"


def test_mudar_categoria_para_a_limitada_avisa(
    client: TestClient, conta: Conta, lazer_com_200: None
) -> None:
    gasto = lancar(client, conta, "Alimentação", 5_000)
    assert gasto["aviso_limite"] is None

    movido = client.patch(
        f"{LANCAMENTOS}/{gasto['id']}", json={"categoria_id": conta.categorias["Lazer"]}
    ).json()

    assert movido["aviso_limite"]["situacao"] == "atencao"


def test_situacao_e_a_do_ciclo_da_data(
    client: TestClient, conta: Conta, lazer_com_200: None
) -> None:
    lancar(client, conta, "Lazer", 5_000)  # ciclo de 05/01 em atenção
    lancar(client, conta, "Salário", 500_000, "2027-01-12")  # novo ciclo, Lazer zerado

    no_novo = lancar(client, conta, "Lazer", 1_000, "2027-01-13")
    no_antigo = lancar(client, conta, "Lazer", 1_000, "2027-01-08")

    assert no_novo["aviso_limite"] is None
    assert no_antigo["aviso_limite"] is None  # já estava em atenção nesse ciclo


def test_estourar_nunca_bloqueia(client: TestClient, conta: Conta, lazer_com_200: None) -> None:
    resposta = lancar(client, conta, "Lazer", 1_000_000)
    assert resposta["aviso_limite"]["situacao"] == "estourado"


def test_reduzir_e_excluir_nao_avisam(
    client: TestClient, conta: Conta, lazer_com_200: None
) -> None:
    gasto = lancar(client, conta, "Lazer", 15_000)  # estoura (35_000)
    reduzido = client.patch(f"{LANCAMENTOS}/{gasto['id']}", json={"valor": 1_000}).json()

    assert reduzido["aviso_limite"] is None
    assert client.delete(f"{LANCAMENTOS}/{gasto['id']}").status_code == 204


def test_entrada_nao_avisa(client: TestClient, conta: Conta, salario: None) -> None:
    assert lancar(client, conta, "Renda extra", 10_000)["aviso_limite"] is None


def test_categoria_sem_limite_nao_avisa(client: TestClient, conta: Conta, salario: None) -> None:
    assert lancar(client, conta, "Moradia", 1_000_000)["aviso_limite"] is None
