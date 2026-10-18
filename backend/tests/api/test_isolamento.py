from collections.abc import Callable
from dataclasses import dataclass

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import Usuario
from app.services.senha import verificar_senha
from tests.conftest import SENHA_PADRAO, Conta


@pytest.fixture
def ana_e_bia(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> tuple[Usuario, Usuario]:
    ana = criar_usuario()
    bia = criar_usuario(email="bia@exemplo.com", nome="Bia Lima", cargo="Designer")
    logar(client, ana)
    return ana, bia


def test_sessao_de_ana_so_le_ana(client: TestClient, ana_e_bia: tuple[Usuario, Usuario]) -> None:
    ana, _ = ana_e_bia
    corpo = client.get("/api/v1/me").json()
    assert corpo["id"] == ana.id
    assert "bia" not in client.get("/api/v1/me").text.lower()


def test_edicao_de_ana_nao_toca_em_bia(
    client: TestClient, ana_e_bia: tuple[Usuario, Usuario], db: Session
) -> None:
    ana, bia = ana_e_bia

    client.patch("/api/v1/me", json={"nome": "Ana Nova", "cargo": "CTO"})

    db.refresh(bia)
    db.refresh(ana)
    assert (bia.nome, bia.cargo) == ("Bia Lima", "Designer")
    assert (ana.nome, ana.cargo) == ("Ana Nova", "CTO")


def test_troca_de_senha_de_ana_nao_toca_em_bia(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    logar: Callable[[TestClient, Usuario], str],
    ana_e_bia: tuple[Usuario, Usuario],
    db: Session,
) -> None:
    _, bia = ana_e_bia
    cliente_bia = novo_client()
    logar(cliente_bia, bia)

    client.put("/api/v1/me/senha", json={"senha_atual": SENHA_PADRAO, "nova_senha": "outra789x"})

    db.refresh(bia)
    assert verificar_senha(bia.senha_hash, SENHA_PADRAO)
    assert cliente_bia.get("/api/v1/me").status_code == 200


def test_nao_ha_rota_que_receba_id_de_usuario(client: TestClient) -> None:
    # O usuário vem sempre da sessão; só as rotas de administrador apontam para outra conta.
    rotas = client.get("/openapi.json").json()["paths"]
    assert all(
        "usuario" not in caminho for caminho in rotas if not caminho.startswith("/api/v1/admin")
    )


# --- Spec 020: contas compartilhadas --------------------------------------------------------------

CC = "/api/v1/contas-compartilhadas"


@dataclass
class ContaDividida:
    """Conta da Ana dividida com a Bia, com cobrança gerada. `dona` é o `client` da Ana."""

    dona: TestClient
    bia: TestClient
    conta: int
    participante: int  # a participação da Bia
    cota: int  # a cota da Bia
    categorias_bia: dict[str, int]


@pytest.fixture
def dividida(
    client: TestClient,
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
) -> ContaDividida:
    ana = criar_conta(client, "ana@exemplo.com")
    bia_client = novo_client()
    bia = criar_conta(bia_client, "bia@exemplo.com")
    for cliente, conta in ((client, ana), (bia_client, bia)):
        resposta = cliente.post(
            "/api/v1/lancamentos",
            json={
                "valor": 500_000,
                "categoria_id": conta.categorias["Salário"],
                "data": "2026-09-01",
            },
        )
        assert resposta.status_code == 201
    corpo = client.post(
        CC,
        json={
            "descricao": "Energia",
            "categoria_id": ana.categorias["Moradia"],
            "modo": "igual",
            "dia_vencimento": 10,
        },
    ).json()
    convidada = client.post(f"{CC}/{corpo['id']}/participantes", json={"email": "bia@exemplo.com"})
    participante = next(p for p in convidada.json()["participantes"] if not p["eh_dono"])
    aceite = bia_client.post(
        f"{CC}/convites/{participante['id']}/aceitar",
        json={"categoria_id": bia.categorias["Moradia"]},
    )
    assert aceite.status_code == 200
    cobranca = client.post(
        f"{CC}/{corpo['id']}/cobrancas", json={"competencia": "2026-10-01", "valor_total": 60_000}
    ).json()
    cota = next(p["cota_id"] for p in cobranca["participantes"] if not p["eh_dono"])
    return ContaDividida(client, bia_client, corpo["id"], participante["id"], cota, bia.categorias)


def test_quem_nao_tem_relacao_com_a_conta_recebe_404_em_todas_as_rotas(
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    dividida: ContaDividida,
) -> None:
    caio_client = novo_client()
    caio = criar_conta(caio_client, "caio@exemplo.com")
    conta, participante, cota = dividida.conta, dividida.participante, dividida.cota
    aceite = {"categoria_id": caio.categorias["Moradia"]}

    rotas: list[tuple[str, str, dict[str, object] | None]] = [
        ("GET", f"{CC}/{conta}", None),
        ("PATCH", f"{CC}/{conta}", {"descricao": "x"}),
        ("POST", f"{CC}/{conta}/participantes", {"email": "z@exemplo.com"}),
        ("PATCH", f"{CC}/{conta}/participantes/{participante}", {"valor": 1}),
        ("DELETE", f"{CC}/{conta}/participantes/{participante}", None),
        ("POST", f"{CC}/{conta}/cobrancas", {"competencia": "2026-11-01", "valor_total": 1}),
        ("POST", f"{CC}/{conta}/sair", None),
        ("POST", f"{CC}/cotas/{cota}/confirmar", None),
        ("POST", f"{CC}/cotas/{cota}/desfazer-confirmacao", None),
        ("POST", f"{CC}/convites/{participante}/aceitar", aceite),
        ("POST", f"{CC}/convites/{participante}/recusar", None),
    ]
    for metodo, url, corpo in rotas:
        resposta = caio_client.request(metodo, url, json=corpo)
        assert resposta.status_code == 404, (metodo, url, resposta.status_code, resposta.text)

    assert caio_client.get(CC).json() == []
    assert caio_client.get(f"{CC}/convites").json() == []


def test_participante_nao_acessa_as_rotas_do_dono(dividida: ContaDividida) -> None:
    conta, participante, cota = dividida.conta, dividida.participante, dividida.cota

    rotas: list[tuple[str, str, dict[str, object] | None]] = [
        ("PATCH", f"{CC}/{conta}", {"descricao": "x"}),
        ("POST", f"{CC}/{conta}/participantes", {"email": "z@exemplo.com"}),
        ("PATCH", f"{CC}/{conta}/participantes/{participante}", {"valor": 1}),
        ("DELETE", f"{CC}/{conta}/participantes/{participante}", None),
        ("POST", f"{CC}/{conta}/cobrancas", {"competencia": "2026-11-01", "valor_total": 1}),
        ("POST", f"{CC}/cotas/{cota}/confirmar", None),
        ("POST", f"{CC}/cotas/{cota}/desfazer-confirmacao", None),
    ]
    for metodo, url, corpo in rotas:
        resposta = dividida.bia.request(metodo, url, json=corpo)
        assert resposta.status_code == 403, (metodo, url, resposta.status_code, resposta.text)
        assert resposta.json()["erro"]["codigo"] == "somente_dono"


def test_participante_nunca_ve_email_nem_valor_de_outro(
    novo_client: Callable[[], TestClient],
    criar_conta: Callable[..., Conta],
    dividida: ContaDividida,
) -> None:
    # Uma terceira pessoa entra na conta: a visão dela mostra a Ana e a Bia, só por nome e status.
    caio_client = novo_client()
    caio = criar_conta(caio_client, "caio@exemplo.com")
    dividida.dona.post(f"{CC}/{dividida.conta}/participantes", json={"email": "caio@exemplo.com"})
    [convite] = caio_client.get(f"{CC}/convites").json()
    caio_client.post(
        f"{CC}/convites/{convite['id']}/aceitar", json={"categoria_id": caio.categorias["Moradia"]}
    )

    resposta = caio_client.get(f"{CC}/{dividida.conta}")

    corpo = resposta.json()
    assert corpo["papel"] == "participante"
    assert sorted(o["nome"] for o in corpo["outros"]) == ["Ana Souza", "Ana Souza"]
    assert all(set(o) == {"nome", "status"} for o in corpo["outros"])
    for proibido in ("ana@exemplo.com", "bia@exemplo.com", "email_convite", "participantes"):
        assert proibido not in resposta.text
    # A cota de outra pessoa (R$ 300,00) também não aparece: só a dele, e ele não tem cobrança.
    assert "30000" not in resposta.text
    assert corpo["minha_cota"] is None


def test_quem_saiu_ou_foi_removido_perde_o_acesso_mas_mantem_o_que_foi_cobrado(
    dividida: ContaDividida,
) -> None:
    assert dividida.bia.post(f"{CC}/{dividida.conta}/sair").status_code == 204

    assert dividida.bia.get(f"{CC}/{dividida.conta}").status_code == 404
    assert dividida.bia.post(f"{CC}/cotas/{dividida.cota}/confirmar").status_code == 404
    # O previsto da cobrança já gerada continua chegando ao ciclo dela.
    ciclo = dividida.bia.get("/api/v1/ciclos/atual").json()
    lancamentos = dividida.bia.get(f"/api/v1/ciclos/{ciclo['inicio']}/lancamentos").json()
    assert [lanc["valor"] for lanc in lancamentos if lanc["descricao"] == "Energia"] == [30_000]
