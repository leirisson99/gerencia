"""US3: cobrança mensal, lançamento previsto da cota e proteção desse lançamento."""

from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any, NamedTuple

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Lancamento
from tests.api.test_contas_compartilhadas import URL, convidar, criar
from tests.conftest import Conta, RelogioFixo

CICLOS = "/api/v1/ciclos"
LANCAMENTOS = "/api/v1/lancamentos"


class Pessoa(NamedTuple):
    client: TestClient
    conta: Conta

    @property
    def email(self) -> str:
        return self.conta.usuario.email


@pytest.fixture(autouse=True)
def hoje_28_de_setembro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 9, 28, 15, 0, tzinfo=UTC)


@pytest.fixture
def pessoa(
    novo_client: Callable[[], TestClient], criar_conta: Callable[..., Conta]
) -> Callable[[str], Pessoa]:
    """Usuário novo, logado em outro navegador e com o salário de setembro já lançado."""

    def _nova(nome: str) -> Pessoa:
        cliente = novo_client()
        conta = criar_conta(cliente, email=f"{nome}@exemplo.com")
        salario(cliente, conta)
        return Pessoa(cliente, conta)

    return _nova


@pytest.fixture
def ana(client: TestClient, criar_conta: Callable[..., Conta]) -> Pessoa:
    conta = criar_conta(client)
    salario(client, conta)
    return Pessoa(client, conta)


def salario(cliente: TestClient, conta: Conta, data: str = "2026-09-01") -> None:
    resposta = cliente.post(
        LANCAMENTOS,
        json={"valor": 500_000, "categoria_id": conta.categorias["Salário"], "data": data},
    )
    assert resposta.status_code == 201, resposta.text


def aceitar(pessoa: Pessoa, conta_conv: int) -> None:
    [convite] = [c for c in pessoa.client.get(f"{URL}/convites").json() if c["id"] == conta_conv]
    resposta = pessoa.client.post(
        f"{URL}/convites/{convite['id']}/aceitar",
        json={"categoria_id": pessoa.conta.categorias["Moradia"]},
    )
    assert resposta.status_code == 200, resposta.text


def convidar_e_aceitar(dona: Pessoa, conta_id: int, convidado: Pessoa, **extra: Any) -> None:
    resposta = convidar(dona.client, conta_id, convidado.email, **extra)
    assert resposta.status_code == 201, resposta.text
    [participante] = [
        p for p in resposta.json()["participantes"] if p["email_convite"] == convidado.email
    ]
    aceitar(convidado, participante["id"])


def conta_com(dona: Pessoa, convidados: list[Pessoa], **alteracoes: Any) -> int:
    conta_id = criar(
        dona.client, dona.conta, categoria_id=dona.conta.categorias["Moradia"], **alteracoes
    ).json()["id"]
    for convidado in convidados:
        convidar_e_aceitar(dona, conta_id, convidado)
    return conta_id


def cobrar(dona: Pessoa, conta_id: int, **corpo: Any) -> httpx.Response:
    return dona.client.post(
        f"{URL}/{conta_id}/cobrancas", json={"competencia": "2026-10-01", **corpo}
    )


def cotas_da(dona: Pessoa, conta_id: int) -> list[int]:
    """Valor da cota de quem tem cota na cobrança em foco, na ordem de entrada."""
    visao = dona.client.get(f"{URL}/{conta_id}").json()
    return [p["cota"] for p in visao["participantes"] if p["cota"] is not None]


def lancamentos_do_ciclo(pessoa: Pessoa) -> list[dict[str, Any]]:
    ciclo = pessoa.client.get(f"{CICLOS}/atual").json()
    return pessoa.client.get(f"{CICLOS}/{ciclo['inicio']}/lancamentos").json()


def da_conta(pessoa: Pessoa, descricao: str = "Energia") -> list[dict[str, Any]]:
    return [lanc for lanc in lancamentos_do_ciclo(pessoa) if lanc["descricao"] == descricao]


# --- cobrança do mês ------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("aceitos", "total", "esperado"),
    [
        (6, 60_000, [10_000] * 6),
        (4, 200_000, [50_000] * 4),
        (3, 10_000, [3_333, 3_333, 3_334]),
        (1, 12_345, [12_345]),
    ],
)
def test_divide_o_total_entre_os_aceitos(
    ana: Pessoa,
    pessoa: Callable[[str], Pessoa],
    aceitos: int,
    total: int,
    esperado: list[int],
) -> None:
    convidados = [pessoa(f"p{n}") for n in range(aceitos - 1)]
    conta_id = conta_com(ana, convidados)

    resposta = cobrar(ana, conta_id, valor_total=total)

    assert resposta.status_code == 201
    assert resposta.json()["valor_total"] == total
    assert cotas_da(ana, conta_id) == esperado
    assert sum(esperado) == total


def test_convidado_que_nao_aceitou_nao_entra_na_divisao(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    bia, caio = pessoa("bia"), pessoa("caio")
    conta_id = conta_com(ana, [bia])
    convidar(ana.client, conta_id, caio.email)  # convidado, mas não aceitou

    corpo = cobrar(ana, conta_id, valor_total=30_000).json()

    assert corpo["qtd_pessoas"] == 2
    assert corpo["qtd_convidados_pendentes"] == 1
    assert cotas_da(ana, conta_id) == [15_000, 15_000]


def test_quem_aceita_depois_nao_altera_a_cobranca_ja_gerada(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    bia, caio = pessoa("bia"), pessoa("caio")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=30_000)

    convidar_e_aceitar(ana, conta_id, caio)

    assert cotas_da(ana, conta_id) == [15_000, 15_000]
    assert caio.client.get(f"{URL}/{conta_id}").json()["minha_cota"] is None


def test_quem_sai_nao_altera_a_cobranca_ja_gerada(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=30_000)

    assert bia.client.post(f"{URL}/{conta_id}/sair").status_code == 204

    visao = ana.client.get(f"{URL}/{conta_id}").json()
    assert sorted(p["cota"] for p in visao["participantes"]) == [15_000, 15_000]


def test_nao_gera_duas_vezes_a_mesma_competencia(ana: Pessoa) -> None:
    conta_id = conta_com(ana, [])
    cobrar(ana, conta_id, valor_total=10_000)

    segunda = cobrar(ana, conta_id, valor_total=20_000)

    assert segunda.status_code == 409
    assert segunda.json()["erro"]["codigo"] == "cobranca_ja_gerada"


def test_mes_ja_cobrado_responde_409_mesmo_com_total_inviavel(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    conta_id = conta_com(ana, [pessoa("bia"), pessoa("caio")])
    cobrar(ana, conta_id, valor_total=10_000)

    segunda = cobrar(ana, conta_id, valor_total=1)  # R$ 0,01 ÷ 3 não dá nem para ratear

    assert segunda.status_code == 409
    assert segunda.json()["erro"]["codigo"] == "cobranca_ja_gerada"


def test_competencia_aceita_qualquer_dia_do_mes(ana: Pessoa) -> None:
    conta_id = conta_com(ana, [])

    resposta = ana.client.post(
        f"{URL}/{conta_id}/cobrancas", json={"competencia": "2026-10-17", "valor_total": 10_000}
    )

    assert resposta.status_code == 201
    repetida = ana.client.post(
        f"{URL}/{conta_id}/cobrancas", json={"competencia": "2026-10-03", "valor_total": 10_000}
    )
    assert repetida.status_code == 409


def test_competencia_so_ate_o_mes_que_vem(ana: Pessoa) -> None:
    conta_id = conta_com(ana, [])

    resposta = ana.client.post(
        f"{URL}/{conta_id}/cobrancas", json={"competencia": "2026-12-01", "valor_total": 10_000}
    )

    assert resposta.status_code == 422
    assert "competencia" in resposta.json()["erro"]["campos"]


def test_conta_variavel_exige_o_total(ana: Pessoa) -> None:
    conta_id = conta_com(ana, [])

    resposta = cobrar(ana, conta_id)

    assert resposta.status_code == 422
    assert "valor_total" in resposta.json()["erro"]["campos"]


def test_falta_informar_o_total_some_depois_da_cobranca(ana: Pessoa) -> None:
    conta_id = conta_com(ana, [])
    assert ana.client.get(f"{URL}/{conta_id}").json()["falta_informar_total"] is True

    cobrar(ana, conta_id, valor_total=10_000)

    visao = ana.client.get(f"{URL}/{conta_id}").json()
    assert visao["falta_informar_total"] is False
    assert visao["valor_total"] == 10_000


def test_conta_fixa_usa_o_valor_fixo_e_recusa_outro_total(ana: Pessoa) -> None:
    conta_id = conta_com(ana, [], valor_fixo=200_000)

    divergente = cobrar(ana, conta_id, valor_total=100_000)
    certa = cobrar(ana, conta_id)

    assert divergente.status_code == 422
    assert certa.status_code == 201
    assert certa.json()["valor_total"] == 200_000


def test_percentual_que_nao_fecha_cem_por_cento(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [], modo="percentual")
    dono = ana.client.get(f"{URL}/{conta_id}").json()["participantes"][0]
    ana.client.patch(f"{URL}/{conta_id}/participantes/{dono['id']}", json={"valor": 6_000})
    convidar_e_aceitar(ana, conta_id, bia, valor=3_000)

    resposta = cobrar(ana, conta_id, valor_total=100_000)

    assert resposta.status_code == 422
    assert "valor_total" in resposta.json()["erro"]["campos"]
    assert "10" in resposta.json()["erro"]["campos"]["valor_total"]  # diferença de 10%


def test_percentual_que_fecha_cem_por_cento(ana: Pessoa, pessoa: Callable[[str], Pessoa]) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [], modo="percentual")
    dono = ana.client.get(f"{URL}/{conta_id}").json()["participantes"][0]
    ana.client.patch(f"{URL}/{conta_id}/participantes/{dono['id']}", json={"valor": 7_000})
    convidar_e_aceitar(ana, conta_id, bia, valor=3_000)

    assert cobrar(ana, conta_id, valor_total=100_000).status_code == 201
    assert cotas_da(ana, conta_id) == [70_000, 30_000]


def test_valores_fixos_que_nao_somam_o_total(ana: Pessoa, pessoa: Callable[[str], Pessoa]) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [], modo="fixo")
    dono = ana.client.get(f"{URL}/{conta_id}").json()["participantes"][0]
    ana.client.patch(f"{URL}/{conta_id}/participantes/{dono['id']}", json={"valor": 50_000})
    convidar_e_aceitar(ana, conta_id, bia, valor=30_000)

    resposta = cobrar(ana, conta_id, valor_total=100_000)

    assert resposta.status_code == 422
    assert "valor_total" in resposta.json()["erro"]["campos"]


def test_so_o_dono_gera_a_cobranca(ana: Pessoa, pessoa: Callable[[str], Pessoa]) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])

    resposta = cobrar(bia, conta_id, valor_total=10_000)

    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "somente_dono"


def test_quem_nao_participa_nao_gera_cobranca(ana: Pessoa, pessoa: Callable[[str], Pessoa]) -> None:
    conta_id = conta_com(ana, [])

    assert cobrar(pessoa("caio"), conta_id, valor_total=10_000).status_code == 404


# --- lançamento previsto da cota -------------------------------------------------------------


def test_o_dono_ja_ve_a_propria_cota_no_ciclo_ao_gerar_a_cobranca(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    conta_id = conta_com(ana, [pessoa("bia")])

    cobrar(ana, conta_id, valor_total=60_000)

    [lancamento] = da_conta(ana)
    assert lancamento["valor"] == 30_000
    assert lancamento["status"] == "previsto"
    assert lancamento["data"] == "2026-10-10"
    assert lancamento["tipo"] == "saida"
    assert lancamento["carteira"] == "pf"


def test_participante_recebe_o_previsto_ao_ler_o_proprio_ciclo(
    ana: Pessoa, pessoa: Callable[[str], Pessoa], db: Session
) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=60_000)
    antes = db.scalar(
        select(func.count())
        .select_from(Lancamento)
        .where(Lancamento.usuario_id == bia.conta.usuario.id)
    )

    [lancamento] = da_conta(bia)

    assert antes == 1  # só o salário: nada foi criado na conta dela por ação da Ana
    assert lancamento["valor"] == 30_000
    assert lancamento["status"] == "previsto"
    assert lancamento["categoria_id"] == bia.conta.categorias["Moradia"]
    assert lancamento["descricao"] == "Energia"
    assert lancamento["cota_id"] is not None  # o front trava valor e data por este campo
    salario_da_bia = next(
        lanc for lanc in lancamentos_do_ciclo(bia) if lanc["descricao"] != "Energia"
    )
    assert salario_da_bia["cota_id"] is None


def test_ler_duas_vezes_nao_duplica(ana: Pessoa, pessoa: Callable[[str], Pessoa]) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=60_000)

    da_conta(bia)
    da_conta(bia)

    assert len(da_conta(bia)) == 1
    assert len(da_conta(ana)) == 1


def test_a_leitura_de_um_usuario_nunca_cria_lancamento_em_outro(
    ana: Pessoa, pessoa: Callable[[str], Pessoa], db: Session
) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=60_000)

    da_conta(ana)

    previstos_da_bia = db.scalar(
        select(func.count())
        .select_from(Lancamento)
        .where(Lancamento.usuario_id == bia.conta.usuario.id, Lancamento.descricao == "Energia")
    )
    assert previstos_da_bia == 0


def test_clt_sem_ciclo_cobrindo_a_data_espera_o_salario(
    ana: Pessoa, novo_client: Callable[[], TestClient], criar_conta: Callable[..., Conta]
) -> None:
    cliente = novo_client()
    sem_salario = Pessoa(cliente, criar_conta(cliente, email="caio@exemplo.com"))
    conta_id = conta_com(ana, [])
    convidar_e_aceitar(ana, conta_id, sem_salario)
    cobrar(ana, conta_id, valor_total=20_000)

    assert sem_salario.client.get(f"{CICLOS}/atual").status_code == 404  # sem ciclo, sem lançamento

    salario(sem_salario.client, sem_salario.conta)
    [lancamento] = da_conta(sem_salario)
    assert lancamento["valor"] == 10_000


def test_quem_saiu_ainda_recebe_o_previsto_da_cobranca_ja_gerada(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=60_000)
    bia.client.post(f"{URL}/{conta_id}/sair")

    [lancamento] = da_conta(bia)

    assert lancamento["valor"] == 30_000
    assert bia.client.get(f"{URL}/{conta_id}").status_code == 404  # sem acesso à conta


def test_saldo_e_gasto_so_contam_a_cota_propria_depois_de_realizada(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=60_000)
    inicio = bia.client.get(f"{CICLOS}/atual").json()["inicio"]
    [lancamento] = da_conta(bia)

    antes = bia.client.get(f"{CICLOS}/{inicio}/resumo").json()
    bia.client.patch(f"{LANCAMENTOS}/{lancamento['id']}", json={"status": "realizado"})
    depois = bia.client.get(f"{CICLOS}/{inicio}/resumo").json()

    assert antes["saidas"] == 0
    assert depois["saidas"] == 30_000
    assert depois["saldo"] == 500_000 - 30_000
    assert [c["total"] for c in depois["saidas_por_categoria"]] == [30_000]


# --- conta de valor fixo -----------------------------------------------------------------------


def passar_dias(relogio: RelogioFixo, dias: int, *clientes: TestClient) -> None:
    for _ in range(dias // 5):
        relogio.avancar(days=5)
        for cliente in clientes:
            cliente.get(f"{URL}/convites")
    relogio.avancar(days=dias % 5)


def test_conta_fixa_so_nasce_a_partir_do_vencimento_e_na_leitura_de_qualquer_participante(
    relogio: RelogioFixo, ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> None:
    relogio.agora = datetime(2026, 9, 5, 15, 0, tzinfo=UTC)
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia], descricao="Aluguel", dia_vencimento=10, valor_fixo=200_000)

    da_conta(bia, "Aluguel")  # dia 5: ainda não venceu
    assert ana.client.get(f"{URL}/{conta_id}").json()["valor_total"] is None

    passar_dias(relogio, 5, ana.client, bia.client)  # dia 10
    [lancamento] = da_conta(bia, "Aluguel")  # a Bia lê, não a dona

    assert lancamento["valor"] == 100_000
    visao = ana.client.get(f"{URL}/{conta_id}").json()
    assert visao["valor_total"] == 200_000
    assert cotas_da(ana, conta_id) == [100_000, 100_000]
    assert len(da_conta(ana, "Aluguel")) == 1


def test_conta_fixa_gerada_pelo_dono_antes_do_vencimento(relogio: RelogioFixo, ana: Pessoa) -> None:
    relogio.agora = datetime(2026, 9, 5, 15, 0, tzinfo=UTC)
    conta_id = conta_com(ana, [], descricao="Aluguel", dia_vencimento=10, valor_fixo=200_000)

    resposta = ana.client.post(f"{URL}/{conta_id}/cobrancas", json={"competencia": "2026-09-01"})

    assert resposta.status_code == 201
    assert resposta.json()["valor_total"] == 200_000


def test_conta_fixa_com_divisao_que_nao_fecha_nao_quebra_a_leitura(
    relogio: RelogioFixo, ana: Pessoa
) -> None:
    relogio.agora = datetime(2026, 9, 20, 15, 0, tzinfo=UTC)
    conta_id = conta_com(
        ana, [], descricao="Aluguel", dia_vencimento=10, valor_fixo=200_000, modo="percentual"
    )

    leitura = ana.client.get(f"{CICLOS}/atual")

    assert leitura.status_code == 200
    assert ana.client.get(f"{URL}/{conta_id}").json()["valor_total"] is None


# --- o lançamento da cota é protegido ----------------------------------------------------------


@pytest.fixture
def cota_da_bia(ana: Pessoa, pessoa: Callable[[str], Pessoa]) -> tuple[Pessoa, dict[str, Any]]:
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=60_000)
    [lancamento] = da_conta(bia)
    return bia, lancamento


@pytest.mark.parametrize(
    "alteracao",
    [{"valor": 1}, {"data": "2026-10-11"}, {"carteira": "pj"}],
)
def test_nao_altera_valor_data_nem_carteira(
    cota_da_bia: tuple[Pessoa, dict[str, Any]], alteracao: dict[str, Any]
) -> None:
    bia, lancamento = cota_da_bia

    resposta = bia.client.patch(f"{LANCAMENTOS}/{lancamento['id']}", json=alteracao)

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamento_de_cota"


def test_nao_troca_para_categoria_de_entrada(cota_da_bia: tuple[Pessoa, dict[str, Any]]) -> None:
    bia, lancamento = cota_da_bia

    resposta = bia.client.patch(
        f"{LANCAMENTOS}/{lancamento['id']}",
        json={"categoria_id": bia.conta.categorias["Renda extra"]},
    )

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamento_de_cota"


def test_nao_exclui_o_lancamento_da_cota(cota_da_bia: tuple[Pessoa, dict[str, Any]]) -> None:
    bia, lancamento = cota_da_bia

    resposta = bia.client.delete(f"{LANCAMENTOS}/{lancamento['id']}")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "lancamento_de_cota"
    assert len(da_conta(bia)) == 1


def test_realiza_desfaz_e_muda_categoria_e_descricao(
    cota_da_bia: tuple[Pessoa, dict[str, Any]],
) -> None:
    bia, lancamento = cota_da_bia
    url = f"{LANCAMENTOS}/{lancamento['id']}"

    assert bia.client.patch(url, json={"status": "realizado"}).status_code == 200
    assert bia.client.patch(url, json={"status": "previsto"}).status_code == 200
    assert bia.client.patch(url, json={"descricao": "Luz de casa"}).status_code == 200
    outra = bia.client.patch(url, json={"categoria_id": bia.conta.categorias["Lazer"]})

    assert outra.status_code == 200
    assert outra.json()["categoria_id"] == bia.conta.categorias["Lazer"]


def test_lancamento_comum_continua_podendo_ser_excluido(
    cota_da_bia: tuple[Pessoa, dict[str, Any]],
) -> None:
    bia, _ = cota_da_bia
    comum = bia.client.post(
        LANCAMENTOS,
        json={"valor": 500, "categoria_id": bia.conta.categorias["Lazer"], "data": "2026-09-10"},
    ).json()

    assert bia.client.delete(f"{LANCAMENTOS}/{comum['id']}").status_code == 204


# --- US4: pagamento e confirmação da cota ------------------------------------------------------


def cota_da(pessoa: Pessoa, conta_id: int) -> dict[str, Any]:
    return pessoa.client.get(f"{URL}/{conta_id}").json()["minha_cota"]


def status_da_bia_para_a_ana(dona: Pessoa, conta_id: int, bia: Pessoa) -> str:
    participantes = dona.client.get(f"{URL}/{conta_id}").json()["participantes"]
    return next(p["status_cota"] for p in participantes if p["email_convite"] == bia.email)


@pytest.fixture
def cobranca_com_bia(
    ana: Pessoa, pessoa: Callable[[str], Pessoa]
) -> tuple[int, Pessoa, dict[str, Any]]:
    """Conta Energia da Ana com a Bia, cobrança de outubro e o previsto da Bia já criado."""
    bia = pessoa("bia")
    conta_id = conta_com(ana, [bia])
    cobrar(ana, conta_id, valor_total=60_000)
    [lancamento] = da_conta(bia)
    return conta_id, bia, lancamento


def realizar(bia: Pessoa, lancamento: dict[str, Any], status: str = "realizado") -> None:
    resposta = bia.client.patch(f"{LANCAMENTOS}/{lancamento['id']}", json={"status": status})
    assert resposta.status_code == 200, resposta.text


def test_status_da_cota_acompanha_o_lancamento_do_titular(
    ana: Pessoa, cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]]
) -> None:
    conta_id, bia, lancamento = cobranca_com_bia
    assert cota_da(bia, conta_id)["status"] == "pendente"
    assert status_da_bia_para_a_ana(ana, conta_id, bia) == "pendente"

    realizar(bia, lancamento)  # "paguei"

    assert cota_da(bia, conta_id)["status"] == "informado"
    assert status_da_bia_para_a_ana(ana, conta_id, bia) == "informado"


def test_dono_confirma_a_cota_informada(
    ana: Pessoa, cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]]
) -> None:
    conta_id, bia, lancamento = cobranca_com_bia
    realizar(bia, lancamento)
    cota_id = cota_da(bia, conta_id)["id"]

    resposta = ana.client.post(f"{URL}/cotas/{cota_id}/confirmar")

    assert resposta.status_code == 200
    assert cota_da(bia, conta_id)["status"] == "confirmado"
    assert status_da_bia_para_a_ana(ana, conta_id, bia) == "confirmado"
    # Os demais participantes veem só o nome e o status, também o confirmado.
    outros = ana.client.get(f"{URL}/{conta_id}").json()
    assert outros["papel"] == "dono"
    visao_da_bia = bia.client.get(f"{URL}/{conta_id}").json()
    assert visao_da_bia["outros"] == [{"nome": "Ana Souza", "status": "pendente"}]


def test_confirmar_nao_toca_em_nenhum_lancamento(
    ana: Pessoa, cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]]
) -> None:
    conta_id, bia, lancamento = cobranca_com_bia
    realizar(bia, lancamento)
    antes = [lanc for lanc in lancamentos_do_ciclo(bia) if lanc["id"] == lancamento["id"]]
    cota_id = cota_da(bia, conta_id)["id"]

    ana.client.post(f"{URL}/cotas/{cota_id}/confirmar")
    ana.client.post(f"{URL}/cotas/{cota_id}/desfazer-confirmacao")

    depois = [lanc for lanc in lancamentos_do_ciclo(bia) if lanc["id"] == lancamento["id"]]
    assert depois == antes


def test_so_o_dono_confirma(cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]]) -> None:
    conta_id, bia, lancamento = cobranca_com_bia
    realizar(bia, lancamento)
    cota_id = cota_da(bia, conta_id)["id"]

    resposta = bia.client.post(f"{URL}/cotas/{cota_id}/confirmar")

    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "somente_dono"


def test_nao_confirma_cota_cujo_lancamento_nao_esta_realizado(
    ana: Pessoa, cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]]
) -> None:
    conta_id, bia, _ = cobranca_com_bia
    cota_id = cota_da(bia, conta_id)["id"]

    resposta = ana.client.post(f"{URL}/cotas/{cota_id}/confirmar")

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "cota_nao_informada"


def test_dono_desfaz_a_confirmacao(
    ana: Pessoa, cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]]
) -> None:
    conta_id, bia, lancamento = cobranca_com_bia
    realizar(bia, lancamento)
    cota_id = cota_da(bia, conta_id)["id"]
    ana.client.post(f"{URL}/cotas/{cota_id}/confirmar")

    resposta = ana.client.post(f"{URL}/cotas/{cota_id}/desfazer-confirmacao")

    assert resposta.status_code == 200
    assert cota_da(bia, conta_id)["status"] == "informado"


def test_cancelar_o_paguei_volta_a_pendente_e_invalida_a_confirmacao(
    ana: Pessoa, cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]]
) -> None:
    conta_id, bia, lancamento = cobranca_com_bia
    realizar(bia, lancamento)
    cota_id = cota_da(bia, conta_id)["id"]
    ana.client.post(f"{URL}/cotas/{cota_id}/confirmar")

    assert cota_da(bia, conta_id)["status"] == "confirmado"

    realizar(bia, lancamento, "previsto")  # a Bia cancela
    assert cota_da(bia, conta_id)["status"] == "pendente"

    realizar(bia, lancamento)  # paga de novo: o dono precisa confirmar outra vez
    assert cota_da(bia, conta_id)["status"] == "informado"


def test_quem_nao_participa_nao_confirma(
    cobranca_com_bia: tuple[int, Pessoa, dict[str, Any]], pessoa: Callable[[str], Pessoa]
) -> None:
    conta_id, bia, lancamento = cobranca_com_bia
    realizar(bia, lancamento)
    cota_id = cota_da(bia, conta_id)["id"]

    resposta = pessoa("intruso").client.post(f"{URL}/cotas/{cota_id}/confirmar")

    assert resposta.status_code == 404


def test_cota_inexistente(ana: Pessoa) -> None:
    assert ana.client.post(f"{URL}/cotas/99999/confirmar").status_code == 404
    assert ana.client.post(f"{URL}/cotas/99999/desfazer-confirmacao").status_code == 404
