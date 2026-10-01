"""Contas de demonstração dos vídeos: a carga inteira passa pela API sem nenhuma recusa."""

from collections.abc import Callable
from datetime import date
from typing import Any

from fastapi.testclient import TestClient

from app.demo import CARLOS, Chamada, datas_de_salario, popular_ana, popular_carlos
from tests.conftest import RelogioFixo

SENHA = "demoGerencia1"


def chamada(cliente: TestClient) -> Chamada:
    def chamar(metodo: str, caminho: str, corpo: object = None) -> tuple[int, Any]:
        resposta = cliente.request(metodo, caminho, json=corpo)
        return resposta.status_code, resposta.json() if resposta.content else {}

    return chamar


def test_datas_de_salario_sao_as_ultimas_ate_hoje() -> None:
    assert datas_de_salario(date(2026, 9, 28)) == [
        date(2026, 7, 5),
        date(2026, 8, 5),
        date(2026, 9, 5),
    ]
    # Antes do dia 5, o salário do mês ainda não caiu; atravessa a virada do ano.
    assert datas_de_salario(date(2026, 2, 3)) == [
        date(2025, 11, 5),
        date(2025, 12, 5),
        date(2026, 1, 5),
    ]


def test_ana_tem_ciclos_limite_quase_estourado_dividas_e_cartela(
    novo_client: Callable[[], TestClient], relogio: RelogioFixo
) -> None:
    cliente = novo_client()
    assert popular_ana(chamada(cliente), relogio.hoje_sp(), SENHA)

    ciclo = cliente.get("/api/v1/ciclos/atual").json()
    assert ciclo["inicio"] == "2026-09-05"
    resumo = cliente.get("/api/v1/ciclos/2026-09-05/resumo").json()
    assert resumo["saldo"] > 0

    lazer = next(c for c in cliente.get("/api/v1/categorias").json() if c["nome"] == "Lazer")
    assert lazer["limite"] == 30_000

    dividas = {d["descricao"]: d for d in cliente.get("/api/v1/dividas").json()}
    assert dividas["Celular novo"]["parcelas_pagas"] == 3
    assert dividas["Empréstimo"]["parcelas_pagas"] == 2

    (cartela,) = cliente.get("/api/v1/cartelas").json()
    assert cartela["guardado"] == 36_000

    lembretes = cliente.get("/api/v1/lembretes").json()
    assert any(i["lancamento"]["descricao"] == "Aluguel" for i in lembretes["atrasados"])
    assert any(i["lancamento"]["descricao"] == "Conta de luz" for i in lembretes["a_vencer"])


def test_carlos_tem_servicos_em_cada_situacao(
    novo_client: Callable[[], TestClient], relogio: RelogioFixo
) -> None:
    cliente = novo_client()
    assert popular_carlos(chamada(cliente), relogio.hoje_sp(), SENHA)

    situacoes = [s["situacao"] for s in cliente.get("/api/v1/servicos").json()]
    assert situacoes.count("recebido") == 3
    assert situacoes.count("atrasado") == 1
    assert situacoes.count("a_receber") == 2


def test_rodar_de_novo_pula_a_conta_existente(
    novo_client: Callable[[], TestClient], relogio: RelogioFixo
) -> None:
    assert popular_carlos(chamada(novo_client()), relogio.hoje_sp(), SENHA)
    assert not popular_carlos(chamada(novo_client()), relogio.hoje_sp(), SENHA)


def test_conta_com_sufixo_e_outra_conta_no_cadastro(
    novo_client: Callable[[], TestClient], relogio: RelogioFixo
) -> None:
    assert popular_carlos(chamada(novo_client()), relogio.hoje_sp(), SENHA)
    outra = CARLOS.com_sufixo("v10")
    cliente = novo_client()
    assert popular_carlos(chamada(cliente), relogio.hoje_sp(), SENHA, outra)
    assert cliente.get("/api/v1/me").json()["email"] == "carlos.demo+v10@exemplo.com"
