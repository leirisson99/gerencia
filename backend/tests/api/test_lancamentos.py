from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Categoria
from tests.conftest import Conta, RelogioFixo

URL = "/api/v1/lancamentos"


@pytest.fixture(autouse=True)
def hoje_15_de_janeiro_de_2027(relogio: RelogioFixo) -> None:
    # As datas da spec (out–dez/2026) ficam no passado; salário futuro é recusado.
    relogio.agora = datetime(2027, 1, 15, 15, 0, tzinfo=UTC)


@pytest.fixture
def conta(client: TestClient, criar_conta: Callable[..., Conta]) -> Conta:
    return criar_conta(client)


def lancar(
    client: TestClient, categoria_id: int, data: str, valor: int = 10_000, **extra: Any
) -> httpx.Response:
    return client.post(
        URL, json={"valor": valor, "categoria_id": categoria_id, "data": data, **extra}
    )


def salario(client: TestClient, conta: Conta, data: str, valor: int = 500_000) -> dict[str, Any]:
    resposta = lancar(client, conta.categorias["Salário"], data, valor)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def gasto(client: TestClient, conta: Conta, data: str, valor: int = 10_000) -> dict[str, Any]:
    resposta = lancar(client, conta.categorias["Alimentação"], data, valor)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def ciclo(client: TestClient, data: str) -> dict[str, Any]:
    return client.get(f"/api/v1/ciclos/{data}").json()


# --- US1: lançar o salário e abrir um ciclo ---------------------------------------------


def test_salario_abre_ciclo_aberto(client: TestClient, conta: Conta) -> None:
    resposta = lancar(
        client, conta.categorias["Salário"], "2026-10-05", 500_000, descricao="Empresa X"
    )

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["valor"] == 500_000
    assert corpo["tipo"] == "entrada"
    assert corpo["status"] == "realizado"
    assert corpo["descricao"] == "Empresa X"
    assert corpo["conta_no_saldo"] is True
    assert corpo["abre_ciclo"] is True

    atual = client.get("/api/v1/ciclos/atual").json()
    assert (atual["inicio"], atual["fim"], atual["aberto"]) == ("2026-10-05", None, True)


def test_segundo_salario_fecha_o_ciclo_anterior(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    salario(client, conta, "2026-11-06")

    assert ciclo(client, "2026-10-05")["fim"] == "2026-11-05"
    assert client.get("/api/v1/ciclos/atual").json()["inicio"] == "2026-11-06"


def test_renda_extra_nao_abre_ciclo(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")

    resposta = lancar(client, conta.categorias["Renda extra"], "2026-10-20", 130_000)

    assert resposta.status_code == 201
    assert resposta.json()["abre_ciclo"] is False
    assert resposta.json()["tipo"] == "entrada"
    assert client.get("/api/v1/ciclos/atual").json()["inicio"] == "2026-10-05"


def test_salario_com_data_futura_e_recusado(client: TestClient, conta: Conta) -> None:
    resposta = lancar(client, conta.categorias["Salário"], "2027-01-16")

    assert resposta.status_code == 422
    assert "data" in resposta.json()["erro"]["campos"]


def test_salario_de_hoje_e_aceito(client: TestClient, conta: Conta) -> None:
    assert lancar(client, conta.categorias["Salário"], "2027-01-15").status_code == 201


def test_salario_previsto_e_recusado(client: TestClient, conta: Conta) -> None:
    resposta = lancar(client, conta.categorias["Salário"], "2026-10-05", status="previsto")

    assert resposta.status_code == 422
    assert "status" in resposta.json()["erro"]["campos"]


def test_tipo_vem_da_categoria(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    assert gasto(client, conta, "2026-10-10")["tipo"] == "saida"


def test_cliente_nao_envia_tipo(client: TestClient, conta: Conta) -> None:
    resposta = lancar(client, conta.categorias["Salário"], "2026-10-05", tipo="saida")

    assert resposta.status_code == 422
    assert "tipo" in resposta.json()["erro"]["campos"]


# --- US2: bloqueio antes do primeiro salário --------------------------------------------


@pytest.mark.parametrize("categoria", ["Alimentação", "Renda extra"])
def test_sem_salario_recusa_outros_lancamentos(
    client: TestClient, conta: Conta, categoria: str
) -> None:
    resposta = lancar(client, conta.categorias[categoria], "2026-10-05")

    assert resposta.status_code == 409
    erro = resposta.json()["erro"]
    assert erro["codigo"] == "salario_necessario"
    assert erro["mensagem"] == "Lance seu salário para abrir o primeiro ciclo."


def test_depois_do_salario_o_gasto_e_aceito(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    assert lancar(client, conta.categorias["Alimentação"], "2026-10-05").status_code == 201


def test_gasto_antes_do_primeiro_ciclo_e_recusado(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")

    resposta = lancar(client, conta.categorias["Alimentação"], "2026-10-01")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "antes_do_primeiro_ciclo"
    assert "05/10/2026" in resposta.json()["erro"]["mensagem"]


def test_gasto_com_data_futura_cai_no_ciclo_aberto(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    assert lancar(client, conta.categorias["Alimentação"], "2027-03-01").status_code == 201


# --- Validação dos campos ---------------------------------------------------------------


@pytest.mark.parametrize("campo", ["valor", "categoria_id", "data"])
def test_campos_obrigatorios(client: TestClient, conta: Conta, campo: str) -> None:
    dados = {"valor": 100, "categoria_id": conta.categorias["Salário"], "data": "2026-10-05"}
    del dados[campo]

    resposta = client.post(URL, json=dados)

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


@pytest.mark.parametrize("valor", [10.5, "1000", 0, -100, 100_000_000_000, True, None])
def test_valor_precisa_ser_inteiro_positivo_em_centavos(
    client: TestClient, conta: Conta, valor: Any
) -> None:
    resposta = lancar(client, conta.categorias["Salário"], "2026-10-05", valor=valor)

    assert resposta.status_code == 422
    assert "valor" in resposta.json()["erro"]["campos"]


def test_valor_maximo_aceito(client: TestClient, conta: Conta) -> None:
    resposta = lancar(client, conta.categorias["Salário"], "2026-10-05", valor=99_999_999_999)
    assert resposta.status_code == 201


def test_data_invalida(client: TestClient, conta: Conta) -> None:
    resposta = lancar(client, conta.categorias["Salário"], "2026-02-30")
    assert resposta.status_code == 422
    assert "data" in resposta.json()["erro"]["campos"]


def test_descricao_vazia_vira_nula(client: TestClient, conta: Conta) -> None:
    corpo = salario_com(client, conta, descricao="   ")
    assert corpo["descricao"] is None


def test_descricao_sem_espacos_nas_pontas(client: TestClient, conta: Conta) -> None:
    assert salario_com(client, conta, descricao="  Empresa X ")["descricao"] == "Empresa X"


def test_descricao_acima_de_200_caracteres(client: TestClient, conta: Conta) -> None:
    resposta = lancar(client, conta.categorias["Salário"], "2026-10-05", descricao="x" * 201)
    assert resposta.status_code == 422
    assert "descricao" in resposta.json()["erro"]["campos"]


def salario_com(client: TestClient, conta: Conta, **extra: Any) -> dict[str, Any]:
    resposta = lancar(client, conta.categorias["Salário"], "2026-10-05", **extra)
    assert resposta.status_code == 201, resposta.text
    return resposta.json()


def test_categoria_inexistente(client: TestClient, conta: Conta) -> None:
    resposta = lancar(client, 999_999_999, "2026-10-05")
    assert resposta.status_code == 404
    assert resposta.json()["erro"]["codigo"] == "nao_encontrado"


def test_categoria_de_outro_usuario_responde_como_inexistente(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    bia = criar_conta(novo_client(), email="bia@exemplo.com")

    resposta = lancar(client, bia.categorias["Salário"], "2026-10-05")

    assert resposta.status_code == 404
    assert resposta.json() == lancar(client, 999_999_999, "2026-10-05").json()


def test_categoria_inativa(client: TestClient, conta: Conta, db: Session) -> None:
    salario(client, conta, "2026-10-05")
    db.execute(
        update(Categoria).where(Categoria.id == conta.categorias["Lazer"]).values(ativa=False)
    )
    db.commit()

    resposta = lancar(client, conta.categorias["Lazer"], "2026-10-10")

    assert resposta.status_code == 422
    assert "categoria_id" in resposta.json()["erro"]["campos"]


def test_exige_login(client: TestClient) -> None:
    assert (
        client.post(URL, json={"valor": 1, "categoria_id": 1, "data": "2026-10-05"}).status_code
        == 401
    )
    assert client.get(f"{URL}/1").status_code == 401


# --- Consultar ---------------------------------------------------------------------------


def test_consulta_um_lancamento(client: TestClient, conta: Conta) -> None:
    criado = salario(client, conta, "2026-10-05")

    resposta = client.get(f"{URL}/{criado['id']}")

    assert resposta.status_code == 200
    # O aviso de limite só existe na resposta da escrita.
    criado.pop("aviso_limite")
    assert resposta.json() == criado


def test_lancamento_inexistente(client: TestClient, conta: Conta) -> None:
    assert client.get(f"{URL}/999999999").status_code == 404


# --- US4: corrigir ou excluir um salário ------------------------------------------------


def test_mudar_data_do_salario_move_o_limite_dos_ciclos(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    segundo = salario(client, conta, "2026-11-06")
    gasto_04_11 = gasto(client, conta, "2026-11-04")

    resposta = client.patch(f"{URL}/{segundo['id']}", json={"data": "2026-11-04"})

    assert resposta.status_code == 200
    assert ciclo(client, "2026-10-05")["fim"] == "2026-11-03"
    assert client.get("/api/v1/ciclos/atual").json()["inicio"] == "2026-11-04"
    ids = [lanc["id"] for lanc in client.get("/api/v1/ciclos/2026-11-04/lancamentos").json()]
    assert gasto_04_11["id"] in ids


def test_excluir_salario_do_meio_une_os_ciclos(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    meio = salario(client, conta, "2026-11-06")
    salario(client, conta, "2026-12-05")

    assert client.delete(f"{URL}/{meio['id']}").status_code == 204

    assert ciclo(client, "2026-10-05")["fim"] == "2026-12-04"
    assert client.get(f"{URL}/{meio['id']}").status_code == 404


def test_excluir_o_unico_salario_com_outros_lancamentos_e_recusado(
    client: TestClient, conta: Conta
) -> None:
    unico = salario(client, conta, "2026-10-05")
    gasto(client, conta, "2026-10-10")

    resposta = client.delete(f"{URL}/{unico['id']}")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamentos_sem_ciclo"
    assert client.get(f"{URL}/{unico['id']}").status_code == 200


def test_excluir_o_unico_salario_sem_outros_lancamentos(client: TestClient, conta: Conta) -> None:
    unico = salario(client, conta, "2026-10-05")

    assert client.delete(f"{URL}/{unico['id']}").status_code == 204
    assert client.get("/api/v1/ciclos/atual").status_code == 404


def test_mover_o_unico_salario_para_depois_de_um_gasto_e_recusado(
    client: TestClient, conta: Conta
) -> None:
    unico = salario(client, conta, "2026-10-05")
    gasto(client, conta, "2026-10-10")

    resposta = client.patch(f"{URL}/{unico['id']}", json={"data": "2026-10-11"})

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamentos_sem_ciclo"


def test_mover_o_primeiro_salario_para_antes_e_aceito(client: TestClient, conta: Conta) -> None:
    unico = salario(client, conta, "2026-10-05")
    gasto(client, conta, "2026-10-10")

    resposta = client.patch(f"{URL}/{unico['id']}", json={"data": "2026-10-01"})

    assert resposta.status_code == 200
    assert client.get("/api/v1/ciclos/atual").json()["inicio"] == "2026-10-01"


def test_mover_salario_para_o_futuro_e_recusado(client: TestClient, conta: Conta) -> None:
    unico = salario(client, conta, "2026-10-05")

    resposta = client.patch(f"{URL}/{unico['id']}", json={"data": "2027-01-16"})

    assert resposta.status_code == 422
    assert "data" in resposta.json()["erro"]["campos"]


def test_tirar_o_unico_salario_da_categoria_salario_e_recusado(
    client: TestClient, conta: Conta
) -> None:
    unico = salario(client, conta, "2026-10-05")
    gasto(client, conta, "2026-10-10")

    resposta = client.patch(
        f"{URL}/{unico['id']}", json={"categoria_id": conta.categorias["Renda extra"]}
    )

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamentos_sem_ciclo"


def test_mudar_um_lancamento_para_salario_abre_ciclo(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    extra = lancar(client, conta.categorias["Renda extra"], "2026-11-06").json()

    resposta = client.patch(
        f"{URL}/{extra['id']}", json={"categoria_id": conta.categorias["Salário"]}
    )

    assert resposta.status_code == 200
    assert resposta.json()["abre_ciclo"] is True
    assert resposta.json()["tipo"] == "entrada"
    assert client.get("/api/v1/ciclos/atual").json()["inicio"] == "2026-11-06"


def test_mudar_categoria_troca_o_tipo(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    lancamento = gasto(client, conta, "2026-10-10")

    resposta = client.patch(
        f"{URL}/{lancamento['id']}", json={"categoria_id": conta.categorias["Renda extra"]}
    )

    assert resposta.json()["tipo"] == "entrada"


def test_mover_gasto_para_antes_do_primeiro_ciclo_e_recusado(
    client: TestClient, conta: Conta
) -> None:
    salario(client, conta, "2026-10-05")
    lancamento = gasto(client, conta, "2026-10-10")

    resposta = client.patch(f"{URL}/{lancamento['id']}", json={"data": "2026-10-04"})

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "antes_do_primeiro_ciclo"


def test_dois_salarios_na_mesma_data(client: TestClient, conta: Conta) -> None:
    primeiro = salario(client, conta, "2026-10-05")
    salario(client, conta, "2026-10-05")
    gasto(client, conta, "2026-10-10")

    assert client.delete(f"{URL}/{primeiro['id']}").status_code == 204
    assert client.get("/api/v1/ciclos/atual").json()["inicio"] == "2026-10-05"


def test_editar_so_muda_os_campos_enviados(client: TestClient, conta: Conta) -> None:
    criado = salario_com(client, conta, descricao="Empresa X")

    resposta = client.patch(f"{URL}/{criado['id']}", json={"valor": 510_000})

    assert resposta.status_code == 200
    assert resposta.json() == {**criado, "valor": 510_000}


def test_editar_remove_a_descricao_com_null(client: TestClient, conta: Conta) -> None:
    criado = salario_com(client, conta, descricao="Empresa X")
    resposta = client.patch(f"{URL}/{criado['id']}", json={"descricao": None})
    assert resposta.json()["descricao"] is None


@pytest.mark.parametrize("campo", ["valor", "categoria_id", "data", "status"])
def test_editar_nao_aceita_null_em_campo_obrigatorio(
    client: TestClient, conta: Conta, campo: str
) -> None:
    criado = salario(client, conta, "2026-10-05")

    resposta = client.patch(f"{URL}/{criado['id']}", json={campo: None})

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_excluir_gasto(client: TestClient, conta: Conta) -> None:
    salario(client, conta, "2026-10-05")
    lancamento = gasto(client, conta, "2026-10-10")

    assert client.delete(f"{URL}/{lancamento['id']}").status_code == 204
    assert client.get(f"{URL}/{lancamento['id']}").status_code == 404


# --- Isolamento --------------------------------------------------------------------------


def test_lancamento_de_outro_usuario_responde_404(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    conta: Conta,
) -> None:
    outro = novo_client()
    bia = criar_conta(outro, email="bia@exemplo.com")
    do_outro = salario(outro, bia, "2026-10-05")
    caminho = f"{URL}/{do_outro['id']}"

    assert client.get(caminho).status_code == 404
    assert client.patch(caminho, json={"valor": 1}).status_code == 404
    assert client.delete(caminho).status_code == 404
    assert outro.get(caminho).json()["valor"] == 500_000
