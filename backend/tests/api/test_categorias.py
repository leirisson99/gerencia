from collections.abc import Callable

from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Categoria
from tests.conftest import Conta

URL = "/api/v1/categorias"

ORDEM_ESPERADA = [
    ("Salário", "entrada", True),
    ("Renda extra", "entrada", False),
    ("Alimentação", "saida", False),
    ("Lazer", "saida", False),
    ("Moradia", "saida", False),
    ("Outros", "saida", False),
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
    assert set(resposta.json()[0]) == {"id", "nome", "tipo", "sistema"}


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
