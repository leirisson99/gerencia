"""Feature 013: serviços a receber."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/servicos"
LANCAMENTOS = "/api/v1/lancamentos"
HOJE = "2026-10-15"


@pytest.fixture(autouse=True)
def hoje_15_de_outubro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 10, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def criar_com_tipo(db: Session, criar_conta: Callable[..., Conta]) -> Callable[..., Conta]:
    def _criar(cliente: TestClient, tipo: str, email: str = "ana@exemplo.com") -> Conta:
        conta = criar_conta(cliente, email)
        conta.usuario.tipo_renda = tipo
        db.commit()
        return conta

    return _criar


@pytest.fixture
def conta(client: TestClient, criar_com_tipo: Callable[..., Conta]) -> Conta:
    return criar_com_tipo(client, "prestador")


def registrar(client: TestClient, conta: Conta, **alteracoes: Any) -> httpx.Response:
    dados: dict[str, Any] = {
        "cliente": "Loja da Maria",
        "valor": 80_000,
        "data_prevista": "2026-10-20",
        "categoria_id": conta.categorias["Renda extra"],
    }
    categoria = alteracoes.pop("categoria", None)
    if categoria:
        dados["categoria_id"] = conta.categorias[categoria]
    dados.update(alteracoes)
    return client.post(URL, json=dados)


def servico(client: TestClient, conta: Conta, **alteracoes: Any) -> dict[str, Any]:
    resposta = registrar(client, conta, **alteracoes)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def receber(client: TestClient, s: dict[str, Any], **dados: Any) -> httpx.Response:
    return client.post(f"{URL}/{s['id']}/recebimento", json={"data": HOJE, **dados})


def lancamento(client: TestClient, s: dict[str, Any]) -> dict[str, Any]:
    resposta = client.get(f"{LANCAMENTOS}/{s['lancamento_id']}")
    assert resposta.status_code == 200, resposta.text
    return resposta.json()


def saldo(client: TestClient, data: str = HOJE) -> int:
    return client.get(f"/api/v1/ciclos/{data}/resumo").json()["saldo"]


# --- US1: registrar ------------------------------------------------------------------------


def test_registra_com_entrada_prevista(client: TestClient, conta: Conta) -> None:
    # US1.1
    resposta = registrar(client, conta, descricao="Site")

    assert resposta.status_code == 201
    s = resposta.json()
    assert s == {
        "id": s["id"],
        "cliente": "Loja da Maria",
        "descricao": "Site",
        "valor": 80_000,
        "data_prevista": "2026-10-20",
        "categoria_id": conta.categorias["Renda extra"],
        "lancamento_id": s["lancamento_id"],
        "situacao": "a_receber",
        "data_recebimento": None,
        "valor_recebido": None,
        "criado_em": s["criado_em"],
    }
    lanc = lancamento(client, s)
    assert (lanc["tipo"], lanc["status"], lanc["valor"], lanc["data"]) == (
        "entrada",
        "previsto",
        80_000,
        "2026-10-20",
    )
    assert lanc["categoria_id"] == conta.categorias["Renda extra"]
    assert lanc["descricao"] == "Loja da Maria — Site"
    assert lanc["servico_id"] == s["id"]
    assert saldo(client) == 0  # previsto não conta


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("cliente", ""),
        ("cliente", "   "),
        ("cliente", "C" * 121),
        ("descricao", "D" * 201),
        ("valor", 0),
        ("valor", -100),
        ("valor", 10.5),
        ("valor", "1000"),
    ],
)
def test_recusa_campos_invalidos(client: TestClient, conta: Conta, campo: str, valor: Any) -> None:
    # US1.2
    resposta = registrar(client, conta, **{campo: valor})

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


@pytest.mark.parametrize("categoria", ["Alimentação", "Salário"])
def test_recusa_categoria_de_saida_ou_salario(
    client: TestClient, conta: Conta, categoria: str
) -> None:
    # US1.3
    resposta = registrar(client, conta, categoria=categoria)

    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["erro"]["campos"]


def test_recusa_categoria_inativa(client: TestClient, conta: Conta) -> None:
    client.patch(f"/api/v1/categorias/{conta.categorias['Renda extra']}", json={"ativa": False})

    resposta = registrar(client, conta)

    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["erro"]["campos"]


def test_data_passada_fica_atrasado(client: TestClient, conta: Conta) -> None:
    # US1.4
    assert servico(client, conta, data_prevista="2026-10-10")["situacao"] == "atrasado"


@pytest.mark.parametrize(
    ("metodo", "caminho"),
    [
        ("GET", ""),
        ("POST", ""),
        ("GET", "/1"),
        ("PATCH", "/1"),
        ("DELETE", "/1"),
        ("POST", "/1/recebimento"),
        ("DELETE", "/1/recebimento"),
    ],
)
def test_clt_nao_acessa(
    client: TestClient, criar_com_tipo: Callable[..., Conta], metodo: str, caminho: str
) -> None:
    # US1.5
    criar_com_tipo(client, "clt")

    resposta = client.request(metodo, URL + caminho, json={})

    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "perfil_sem_servicos"


def test_rotas_exigem_sessao(client: TestClient) -> None:
    assert client.get(URL).status_code == 401


def test_clt_prestador_sem_salario(
    client: TestClient, criar_com_tipo: Callable[..., Conta]
) -> None:
    # US1.6
    misto = criar_com_tipo(client, "clt_prestador")

    resposta = registrar(client, misto)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "salario_necessario"


def test_clt_prestador_com_salario(
    client: TestClient, criar_com_tipo: Callable[..., Conta]
) -> None:
    misto = criar_com_tipo(client, "clt_prestador")
    client.post(
        LANCAMENTOS,
        json={"valor": 500_000, "categoria_id": misto.categorias["Salário"], "data": "2026-10-05"},
    )

    s = servico(client, misto)
    assert receber(client, s).status_code == 200
    assert saldo(client) == 580_000


# --- US2: receber e desfazer ---------------------------------------------------------------


def test_receber_valor_combinado(client: TestClient, conta: Conta) -> None:
    # US2.1
    s = servico(client, conta)

    resposta = receber(client, s, data="2026-10-14")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert (corpo["situacao"], corpo["data_recebimento"], corpo["valor_recebido"]) == (
        "recebido",
        "2026-10-14",
        80_000,
    )
    lanc = lancamento(client, s)
    assert (lanc["status"], lanc["data"], lanc["valor"]) == ("realizado", "2026-10-14", 80_000)
    assert saldo(client) == 80_000


def test_receber_valor_diferente(client: TestClient, conta: Conta) -> None:
    # US2.2
    s = servico(client, conta)

    corpo = receber(client, s, valor=75_000).json()

    assert (corpo["valor"], corpo["valor_recebido"]) == (80_000, 75_000)
    assert saldo(client) == 75_000


def test_receber_com_data_futura(client: TestClient, conta: Conta) -> None:
    # US2.3
    resposta = receber(client, servico(client, conta), data="2026-10-16")

    assert resposta.status_code == 422
    assert "data" in resposta.json()["erro"]["campos"]


def test_receber_duas_vezes(client: TestClient, conta: Conta) -> None:
    # US2.4
    s = servico(client, conta)
    receber(client, s)

    resposta = receber(client, s)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "servico_recebido"


def test_desfazer_recebimento(client: TestClient, conta: Conta) -> None:
    # US2.5
    s = servico(client, conta, data_prevista="2026-10-10")
    receber(client, s, valor=75_000)

    resposta = client.delete(f"{URL}/{s['id']}/recebimento")

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert (corpo["situacao"], corpo["data_recebimento"], corpo["valor_recebido"]) == (
        "atrasado",
        None,
        None,
    )
    lanc = lancamento(client, s)
    assert (lanc["status"], lanc["data"], lanc["valor"]) == ("previsto", "2026-10-10", 80_000)
    assert saldo(client) == 0


def test_desfazer_sem_ter_recebido(client: TestClient, conta: Conta) -> None:
    # US2.6
    resposta = client.delete(f"{URL}/{servico(client, conta)['id']}/recebimento")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "servico_nao_recebido"


def test_clt_prestador_recebe_antes_do_primeiro_salario(
    client: TestClient, criar_com_tipo: Callable[..., Conta]
) -> None:
    misto = criar_com_tipo(client, "clt_prestador")
    client.post(
        LANCAMENTOS,
        json={"valor": 500_000, "categoria_id": misto.categorias["Salário"], "data": "2026-10-05"},
    )
    s = servico(client, misto)

    resposta = receber(client, s, data="2026-10-04")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "antes_do_primeiro_ciclo"


# --- US3: listar ---------------------------------------------------------------------------


@pytest.fixture
def tres_servicos(client: TestClient, conta: Conta) -> dict[str, dict[str, Any]]:
    a_receber = servico(client, conta, cliente="B", data_prevista="2026-10-25")
    atrasado = servico(client, conta, cliente="A", data_prevista="2026-10-01")
    recebido = servico(client, conta, cliente="C", data_prevista="2026-10-15")
    receber(client, recebido)
    return {"a_receber": a_receber, "atrasado": atrasado, "recebido": recebido}


def test_lista_por_data_prevista(
    client: TestClient, tres_servicos: dict[str, dict[str, Any]]
) -> None:
    # US3.1
    lista = client.get(URL).json()

    assert [(s["cliente"], s["situacao"]) for s in lista] == [
        ("A", "atrasado"),
        ("C", "recebido"),
        ("B", "a_receber"),
    ]


@pytest.mark.parametrize("situacao", ["a_receber", "atrasado", "recebido"])
def test_filtra_por_situacao(
    client: TestClient, tres_servicos: dict[str, dict[str, Any]], situacao: str
) -> None:
    # US3.2
    lista = client.get(URL, params={"situacao": situacao}).json()

    assert [s["id"] for s in lista] == [tres_servicos[situacao]["id"]]


def test_situacao_invalida(client: TestClient, conta: Conta) -> None:
    assert client.get(URL, params={"situacao": "pago"}).status_code == 422


def test_previsto_para_hoje_esta_a_receber(client: TestClient, conta: Conta) -> None:
    # US3.3
    assert servico(client, conta, data_prevista=HOJE)["situacao"] == "a_receber"


def test_recebido_mostra_data_e_valor(
    client: TestClient, tres_servicos: dict[str, dict[str, Any]]
) -> None:
    # US3.4
    corpo = client.get(f"{URL}/{tres_servicos['recebido']['id']}").json()

    assert (corpo["data_recebimento"], corpo["valor_recebido"]) == (HOJE, 80_000)


def test_isolamento(
    client: TestClient,
    conta: Conta,
    novo_client: Callable[[], TestClient],
    criar_com_tipo: Callable[..., Conta],
) -> None:
    # US3.5
    s = servico(client, conta)
    outro = novo_client()
    bia = criar_com_tipo(outro, "prestador", "bia@exemplo.com")

    assert outro.get(URL).json() == []
    for metodo, caminho, corpo in [
        ("GET", "", None),
        ("PATCH", "", {"valor": 1}),
        ("DELETE", "", None),
        ("POST", "/recebimento", {"data": HOJE}),
        ("DELETE", "/recebimento", None),
    ]:
        resposta = outro.request(metodo, f"{URL}/{s['id']}{caminho}", json=corpo)
        assert resposta.status_code == 404, (metodo, caminho)
    # Categoria de outro usuário também não é encontrada.
    resposta = registrar(outro, bia, categoria_id=conta.categorias["Renda extra"])
    assert resposta.status_code == 404
    assert lancamento(client, s)["status"] == "previsto"


# --- US4: corrigir ou excluir --------------------------------------------------------------


def test_editar_sincroniza_o_previsto(client: TestClient, conta: Conta) -> None:
    # US4.1 e US4.2
    client.post("/api/v1/categorias", json={"nome": "Serviços", "tipo": "entrada"})
    servicos_id = client.get("/api/v1/categorias").json()
    categoria = next(c["id"] for c in servicos_id if c["nome"] == "Serviços")
    s = servico(client, conta, descricao="Site")

    resposta = client.patch(
        f"{URL}/{s['id']}",
        json={
            "valor": 90_000,
            "data_prevista": "2026-10-25",
            "cliente": "Maria ME",
            "categoria_id": categoria,
        },
    )

    assert resposta.status_code == 200, resposta.text
    corpo = resposta.json()
    assert (corpo["valor"], corpo["data_prevista"], corpo["cliente"]) == (
        90_000,
        "2026-10-25",
        "Maria ME",
    )
    lanc = lancamento(client, s)
    assert (lanc["valor"], lanc["data"], lanc["categoria_id"], lanc["descricao"]) == (
        90_000,
        "2026-10-25",
        categoria,
        "Maria ME — Site",
    )


def test_editar_remove_descricao(client: TestClient, conta: Conta) -> None:
    s = servico(client, conta, descricao="Site")

    corpo = client.patch(f"{URL}/{s['id']}", json={"descricao": None}).json()

    assert corpo["descricao"] is None
    assert lancamento(client, s)["descricao"] == "Loja da Maria"


@pytest.mark.parametrize("campo", ["cliente", "valor", "data_prevista", "categoria_id"])
def test_editar_recusa_null(client: TestClient, conta: Conta, campo: str) -> None:
    resposta = client.patch(f"{URL}/{servico(client, conta)['id']}", json={campo: None})

    assert resposta.status_code == 422


def test_editar_recusa_categoria_de_saida(client: TestClient, conta: Conta) -> None:
    s = servico(client, conta)

    resposta = client.patch(
        f"{URL}/{s['id']}", json={"categoria_id": conta.categorias["Alimentação"]}
    )

    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["erro"]["campos"]


def test_excluir(client: TestClient, conta: Conta) -> None:
    # US4.3
    s = servico(client, conta)

    assert client.delete(f"{URL}/{s['id']}").status_code == 204
    assert client.get(f"{URL}/{s['id']}").status_code == 404
    assert client.get(f"{LANCAMENTOS}/{s['lancamento_id']}").status_code == 404


def test_recebido_nao_edita_nem_exclui(client: TestClient, conta: Conta) -> None:
    # US4.4
    s = servico(client, conta)
    receber(client, s)

    for resposta in (
        client.patch(f"{URL}/{s['id']}", json={"valor": 1_000}),
        client.delete(f"{URL}/{s['id']}"),
    ):
        assert resposta.status_code == 409
        assert resposta.json()["erro"]["codigo"] == "servico_recebido"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [("valor", 1_000), ("status", "realizado"), ("data", "2026-10-21"), ("categoria_id", None)],
)
def test_lancamento_do_servico_travado(
    client: TestClient, conta: Conta, campo: str, valor: Any
) -> None:
    # US4.5
    s = servico(client, conta)
    if campo == "categoria_id":
        client.post("/api/v1/categorias", json={"nome": "Serviços", "tipo": "entrada"})
        categorias = client.get("/api/v1/categorias").json()
        valor = next(c["id"] for c in categorias if c["nome"] == "Serviços")

    resposta = client.patch(f"{LANCAMENTOS}/{s['lancamento_id']}", json={campo: valor})

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_lancamento_do_servico_aceita_descricao(client: TestClient, conta: Conta) -> None:
    s = servico(client, conta)

    resposta = client.patch(f"{LANCAMENTOS}/{s['lancamento_id']}", json={"descricao": "Obs"})

    assert resposta.status_code == 200


def test_lancamento_do_servico_nao_e_excluido(client: TestClient, conta: Conta) -> None:
    s = servico(client, conta)

    resposta = client.delete(f"{LANCAMENTOS}/{s['lancamento_id']}")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamento_de_servico"


# --- US5: deixar de prestar serviço --------------------------------------------------------


@pytest.fixture
def misto_com_salario(client: TestClient, criar_com_tipo: Callable[..., Conta]) -> Conta:
    misto = criar_com_tipo(client, "clt_prestador")
    client.post(
        LANCAMENTOS,
        json={"valor": 500_000, "categoria_id": misto.categorias["Salário"], "data": "2026-10-05"},
    )
    return misto


def test_pendente_impede_virar_clt(client: TestClient, misto_com_salario: Conta) -> None:
    # US5.1
    servico(client, misto_com_salario)

    resposta = client.patch("/api/v1/me", json={"tipo_renda": "clt"})

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "servicos_pendentes"


def test_so_recebidos_vira_clt_e_destrava(client: TestClient, misto_com_salario: Conta) -> None:
    # US5.2
    s = servico(client, misto_com_salario)
    receber(client, s)

    assert client.patch("/api/v1/me", json={"tipo_renda": "clt"}).status_code == 200
    assert saldo(client) == 580_000
    resposta = client.patch(f"{LANCAMENTOS}/{s['lancamento_id']}", json={"valor": 81_000})
    assert resposta.status_code == 200, resposta.text


def test_prestador_com_pendente_vira_clt_prestador(client: TestClient, conta: Conta) -> None:
    # US5.3
    client.post(
        LANCAMENTOS,
        json={"valor": 500_000, "categoria_id": conta.categorias["Salário"], "data": "2026-10-01"},
    )
    servico(client, conta)

    assert client.patch("/api/v1/me", json={"tipo_renda": "clt_prestador"}).status_code == 200
    assert len(client.get(URL).json()) == 1
