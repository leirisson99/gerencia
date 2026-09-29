from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.models import Usuario

URL = "/api/v1/me"


@pytest.fixture
def logado(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> Usuario:
    usuario = criar_usuario(data_nascimento=date(1995, 3, 15))
    logar(client, usuario)
    return usuario


def test_ve_os_proprios_dados_sem_senha(client: TestClient, logado: Usuario) -> None:
    corpo = client.get(URL).json()

    assert corpo == {
        "id": logado.id,
        "nome": "Ana Souza",
        "email": "ana@exemplo.com",
        "telefone": "11987654321",
        "cargo": "Desenvolvedora",
        "data_nascimento": "1995-03-15",
        "troca_senha_obrigatoria": False,
        "papel": "usuario",
        "criado_em": corpo["criado_em"],
    }


def test_edita_nome_telefone_cargo_e_data(client: TestClient, logado: Usuario) -> None:
    resposta = client.patch(
        URL,
        json={
            "nome": "  Ana S. ",
            "telefone": "(21) 3333-4444",
            "cargo": "Tech lead",
            "data_nascimento": "1990-01-02",
        },
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["nome"] == "Ana S."
    assert corpo["telefone"] == "2133334444"
    assert corpo["cargo"] == "Tech lead"
    assert corpo["data_nascimento"] == "1990-01-02"
    assert client.get(URL).json()["cargo"] == "Tech lead"


def test_so_altera_os_campos_enviados(client: TestClient, logado: Usuario) -> None:
    corpo = client.patch(URL, json={"cargo": "Tech lead"}).json()
    assert corpo["nome"] == "Ana Souza"
    assert corpo["telefone"] == "11987654321"
    assert corpo["data_nascimento"] == "1995-03-15"


def test_patch_vazio_nao_muda_nada(client: TestClient, logado: Usuario) -> None:
    antes = client.get(URL).json()
    resposta = client.patch(URL, json={})
    assert resposta.status_code == 200
    assert resposta.json() == antes


def test_remove_a_data_de_nascimento(client: TestClient, logado: Usuario) -> None:
    resposta = client.patch(URL, json={"data_nascimento": None})
    assert resposta.status_code == 200
    assert resposta.json()["data_nascimento"] is None


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("nome", "   "),
        ("nome", None),
        ("cargo", ""),
        ("cargo", None),
        ("telefone", "123"),
        ("telefone", None),
        ("data_nascimento", "2026-09-29"),
        ("data_nascimento", "1899-12-31"),
    ],
)
def test_recusa_valores_invalidos(
    client: TestClient, logado: Usuario, campo: str, valor: str | None
) -> None:
    resposta = client.patch(URL, json={campo: valor})

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


@pytest.mark.parametrize("campo", ["email", "papel", "senha", "troca_senha_obrigatoria"])
def test_recusa_campos_que_nao_podem_ser_editados(
    client: TestClient, logado: Usuario, campo: str
) -> None:
    resposta = client.patch(URL, json={campo: "x"})

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]
    assert client.get(URL).json()["email"] == "ana@exemplo.com"


def test_editar_exige_login(client: TestClient) -> None:
    assert client.patch(URL, json={"cargo": "x"}).status_code == 401


def test_editar_bloqueado_com_troca_obrigatoria(
    client: TestClient,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> None:
    logar(client, criar_usuario(troca_senha_obrigatoria=True))

    resposta = client.patch(URL, json={"cargo": "Outro"})

    assert resposta.status_code == 403
    assert resposta.json()["erro"]["codigo"] == "troca_senha_obrigatoria"
