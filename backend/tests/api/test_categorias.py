from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Categoria
from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/categorias"

ORDEM_ESPERADA = [
    ("Salário", "entrada", True),
    ("Renda extra", "entrada", False),
    ("Alimentação", "saida", False),
    ("Lazer", "saida", False),
    ("Moradia", "saida", False),
    ("Outros", "saida", False),
    ("Poupança", "saida", True),
    ("Saúde", "saida", False),
    ("Transporte", "saida", False),
]


def test_lista_as_categorias_iniciais_em_ordem(
    client: TestClient, criar_conta: Callable[..., Conta]
) -> None:
    criar_conta(client)

    resposta = client.get(URL)

    assert resposta.status_code == 200
    assert [(c["nome"], c["tipo"], c["sistema"]) for c in resposta.json()] == ORDEM_ESPERADA
    assert set(resposta.json()[0]) == {"id", "nome", "tipo", "sistema", "ativa"}


def test_nao_lista_categorias_inativas(
    client: TestClient, criar_conta: Callable[..., Conta], db: Session
) -> None:
    conta = criar_conta(client)
    db.execute(
        update(Categoria).where(Categoria.id == conta.categorias["Lazer"]).values(ativa=False)
    )
    db.commit()

    nomes = [c["nome"] for c in client.get(URL).json()]

    assert "Lazer" not in nomes


def test_so_lista_as_categorias_do_proprio_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
) -> None:
    ana = criar_conta(client)
    criar_conta(novo_client(), email="bia@exemplo.com")

    ids = {c["id"] for c in client.get(URL).json()}

    assert ids == set(ana.categorias.values())


def test_exige_login(client: TestClient) -> None:
    assert client.get(URL).status_code == 401


# --- 005: criar, renomear, desativar ------------------------------------------------------


@pytest.fixture(autouse=True)
def hoje_15_de_janeiro_de_2027(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2027, 1, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


def lancar(client: TestClient, categoria_id: int, data: str, valor: int = 10_000):
    return client.post(
        "/api/v1/lancamentos", json={"valor": valor, "categoria_id": categoria_id, "data": data}
    )


def test_cria_categoria(client: TestClient, conta: Conta) -> None:
    resposta = client.post(URL, json={"nome": "  Pets ", "tipo": "saida"})

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert (corpo["nome"], corpo["tipo"], corpo["sistema"], corpo["ativa"]) == (
        "Pets",
        "saida",
        False,
        True,
    )
    assert "Pets" in [c["nome"] for c in client.get(URL).json()]
    lancar(client, conta.categorias["Salário"], "2026-10-05")
    gasto = lancar(client, corpo["id"], "2026-10-06")
    assert gasto.status_code == 201
    assert gasto.json()["tipo"] == "saida"


@pytest.mark.parametrize("nome", ["Moradia", "moradia", " MORADIA ", "Salário", "salário"])
def test_nome_repetido(client: TestClient, conta: Conta, nome: str) -> None:
    resposta = client.post(URL, json={"nome": nome, "tipo": "saida"})

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "categoria_existente"


def test_mesmo_nome_em_usuarios_diferentes(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    outro = novo_client()
    criar_conta(outro, email="bia@exemplo.com")

    assert client.post(URL, json={"nome": "Pets", "tipo": "saida"}).status_code == 201
    assert outro.post(URL, json={"nome": "Pets", "tipo": "saida"}).status_code == 201


@pytest.mark.parametrize(
    ("campo", "corpo"),
    [
        ("nome", {"nome": "   ", "tipo": "saida"}),
        ("nome", {"nome": "x" * 61, "tipo": "saida"}),
        ("tipo", {"nome": "Pets", "tipo": "despesa"}),
        ("nome", {"tipo": "saida"}),
        ("tipo", {"nome": "Pets"}),
        ("sistema", {"nome": "Pets", "tipo": "saida", "sistema": True}),
    ],
)
def test_validacao_ao_criar(client: TestClient, conta: Conta, campo: str, corpo: dict) -> None:
    resposta = client.post(URL, json=corpo)

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_renomear_mantem_lancamentos_e_aparece_no_resumo(client: TestClient, conta: Conta) -> None:
    lancar(client, conta.categorias["Salário"], "2026-10-05", 500_000)
    gasto = lancar(client, conta.categorias["Outros"], "2026-10-06").json()

    resposta = client.patch(f"{URL}/{conta.categorias['Outros']}", json={"nome": "Diversos"})

    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "Diversos"
    assert (
        client.get(f"/api/v1/lancamentos/{gasto['id']}").json()["categoria_id"]
        == (conta.categorias["Outros"])
    )
    resumo = client.get("/api/v1/ciclos/2026-10-05/resumo").json()
    assert [c["nome"] for c in resumo["saidas_por_categoria"]] == ["Diversos"]


def test_renomear_para_nome_existente(client: TestClient, conta: Conta) -> None:
    resposta = client.patch(f"{URL}/{conta.categorias['Lazer']}", json={"nome": "saúde"})
    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "categoria_existente"


def test_renomear_mudando_so_maiusculas(client: TestClient, conta: Conta) -> None:
    resposta = client.patch(f"{URL}/{conta.categorias['Lazer']}", json={"nome": "LAZER"})
    assert resposta.status_code == 200
    assert resposta.json()["nome"] == "LAZER"


@pytest.mark.parametrize("categoria", ["Salário", "Poupança"])
@pytest.mark.parametrize("corpo", [{"nome": "Remuneração"}, {"ativa": False}])
def test_categorias_do_sistema_sao_protegidas(
    client: TestClient, conta: Conta, corpo: dict, categoria: str
) -> None:
    resposta = client.patch(f"{URL}/{conta.categorias[categoria]}", json=corpo)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "categoria_do_sistema"


def test_tipo_nao_muda(client: TestClient, conta: Conta) -> None:
    resposta = client.patch(f"{URL}/{conta.categorias['Lazer']}", json={"tipo": "entrada"})
    assert resposta.status_code == 422
    assert "tipo" in resposta.json()["erro"]["campos"]


@pytest.mark.parametrize("campo", ["nome", "ativa"])
def test_patch_nao_aceita_null(client: TestClient, conta: Conta, campo: str) -> None:
    resposta = client.patch(f"{URL}/{conta.categorias['Lazer']}", json={campo: None})
    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_desativar_e_reativar(client: TestClient, conta: Conta) -> None:
    lancar(client, conta.categorias["Salário"], "2026-10-05", 500_000)
    antigo = lancar(client, conta.categorias["Transporte"], "2026-10-06", 3_000).json()
    caminho = f"{URL}/{conta.categorias['Transporte']}"

    desativada = client.patch(caminho, json={"ativa": False})

    assert desativada.status_code == 200
    assert desativada.json()["ativa"] is False
    assert "Transporte" not in [c["nome"] for c in client.get(URL).json()]
    todas = client.get(URL, params={"incluir_inativas": True}).json()
    assert {c["nome"]: c["ativa"] for c in todas}["Transporte"] is False
    assert lancar(client, conta.categorias["Transporte"], "2026-10-07").status_code == 422
    assert client.get(f"/api/v1/lancamentos/{antigo['id']}").status_code == 200
    resumo = client.get("/api/v1/ciclos/2026-10-05/resumo").json()
    assert resumo["saidas"] == 3_000

    assert client.patch(caminho, json={"ativa": True}).json()["ativa"] is True
    assert "Transporte" in [c["nome"] for c in client.get(URL).json()]
    assert lancar(client, conta.categorias["Transporte"], "2026-10-07").status_code == 201


def test_categoria_de_outro_usuario(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    bia = criar_conta(novo_client(), email="bia@exemplo.com")

    resposta = client.patch(f"{URL}/{bia.categorias['Lazer']}", json={"nome": "Meu"})

    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "nao_encontrado"


def test_categoria_inexistente(client: TestClient, conta: Conta) -> None:
    assert client.patch(f"{URL}/999999999", json={"nome": "X"}).status_code == 404


def test_criar_e_editar_exigem_login(client: TestClient) -> None:
    assert client.post(URL, json={"nome": "Pets", "tipo": "saida"}).status_code == 401
    assert client.patch(f"{URL}/1", json={"nome": "X"}).status_code == 401
