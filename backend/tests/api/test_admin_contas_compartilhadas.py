"""Spec 020: o administrador vê só contagens do módulo, nunca nomes, e-mails nem valores."""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient

from tests.api.conftest import USUARIOS
from tests.conftest import Conta, RelogioFixo

CC = "/api/v1/contas-compartilhadas"
RESUMO = "/api/v1/admin/resumo"
SEGREDO_CONTA = "SEGREDO-CONTA"
TOTAL = 654_322  # cada uma das duas partes é 327.161


@pytest.fixture(autouse=True)
def hoje_28_de_setembro(relogio: RelogioFixo) -> None:
    relogio.agora = datetime(2026, 9, 28, 15, 0, tzinfo=UTC)


def salario(cliente: TestClient, conta: Conta) -> None:
    resposta = cliente.post(
        "/api/v1/lancamentos",
        json={"valor": 500_000, "categoria_id": conta.categorias["Salário"], "data": "2026-09-01"},
    )
    assert resposta.status_code == 201, resposta.text


@pytest.fixture
def ana_e_bia(
    novo_client: Callable[[], TestClient], criar_conta: Callable[..., Conta]
) -> tuple[tuple[TestClient, Conta], tuple[TestClient, Conta]]:
    """Ana é dona de uma conta dividida com a Bia; a cobrança saiu e a Bia já leu o ciclo."""
    cliente_ana, cliente_bia = novo_client(), novo_client()
    ana = criar_conta(cliente_ana, "ana@exemplo.com")
    bia = criar_conta(cliente_bia, "bia@exemplo.com")
    salario(cliente_ana, ana)
    salario(cliente_bia, bia)

    conta = cliente_ana.post(
        CC,
        json={
            "descricao": SEGREDO_CONTA,
            "categoria_id": ana.categorias["Moradia"],
            "modo": "igual",
            "dia_vencimento": 10,
        },
    ).json()
    cliente_ana.post(f"{CC}/{conta['id']}/participantes", json={"email": "bia@exemplo.com"})
    [convite] = cliente_bia.get(f"{CC}/convites").json()
    cliente_bia.post(
        f"{CC}/convites/{convite['id']}/aceitar", json={"categoria_id": bia.categorias["Moradia"]}
    )
    cliente_ana.post(
        f"{CC}/{conta['id']}/cobrancas", json={"competencia": "2026-10-01", "valor_total": TOTAL}
    )
    cliente_bia.get("/api/v1/ciclos/atual")  # materializa o previsto da Bia
    return (cliente_ana, ana), (cliente_bia, bia)


def test_contagens_do_modulo_no_detalhe_da_conta(
    cliente_admin: TestClient, ana_e_bia: tuple[tuple[TestClient, Conta], tuple[TestClient, Conta]]
) -> None:
    (_, ana), (_, bia) = ana_e_bia

    da_ana = cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}").json()["contagens"]
    da_bia = cliente_admin.get(f"{USUARIOS}/{bia.usuario.id}").json()["contagens"]

    assert (da_ana["contas_compartilhadas"], da_ana["participacoes"]) == (1, 0)
    assert (da_bia["contas_compartilhadas"], da_bia["participacoes"]) == (0, 1)
    # O previsto da cota é um lançamento automático, não um digitado.
    assert da_ana["lancamentos_gerados"] == 1
    assert da_bia["lancamentos_gerados"] == 1
    assert da_ana["lancamentos_manuais"] == da_bia["lancamentos_manuais"] == 1  # o salário


def test_resumo_conta_quem_usa_o_modulo(
    cliente_admin: TestClient, ana_e_bia: tuple[tuple[TestClient, Conta], tuple[TestClient, Conta]]
) -> None:
    uso = cliente_admin.get(RESUMO).json()["uso_funcionalidades"]

    assert {"funcionalidade": "contas_compartilhadas", "contas": 2} in uso


def test_admin_nao_ve_nome_email_descricao_nem_valor_do_modulo(
    cliente_admin: TestClient, ana_e_bia: tuple[tuple[TestClient, Conta], tuple[TestClient, Conta]]
) -> None:
    (_, ana), (_, bia) = ana_e_bia

    detalhe_ana = cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}").text
    detalhe_bia = cliente_admin.get(f"{USUARIOS}/{bia.usuario.id}").text
    resumo = cliente_admin.get(RESUMO).text

    for texto in (detalhe_ana, detalhe_bia, resumo):
        assert SEGREDO_CONTA not in texto
        assert "327161" not in texto
        assert str(TOTAL) not in texto
    # O detalhe de uma conta não revela o e-mail de quem divide a conta com ela.
    assert "bia@exemplo.com" not in detalhe_ana
    assert "ana@exemplo.com" not in detalhe_bia


def test_eventos_do_modulo_guardam_so_o_tipo(
    cliente_admin: TestClient, ana_e_bia: tuple[tuple[TestClient, Conta], tuple[TestClient, Conta]]
) -> None:
    (_, ana), (_, bia) = ana_e_bia

    da_ana = cliente_admin.get(f"{USUARIOS}/{ana.usuario.id}/eventos").json()
    da_bia = cliente_admin.get(f"{USUARIOS}/{bia.usuario.id}/eventos").json()

    tipos_ana = {e["tipo"] for e in da_ana["itens"]}
    tipos_bia = {e["tipo"] for e in da_bia["itens"]}
    assert {"conta_compartilhada_criada", "cobranca_gerada"} <= tipos_ana
    assert "convite_aceito" in tipos_bia
    for evento in (*da_ana["itens"], *da_bia["itens"]):
        assert set(evento) == {"tipo", "ocorrido_em"}  # nunca o conteúdo da ação
