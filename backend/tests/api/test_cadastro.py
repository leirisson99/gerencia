from collections.abc import Callable
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Categoria, Usuario

URL = "/api/v1/auth/cadastro"


def dados_validos(**alteracoes: Any) -> dict[str, Any]:
    dados: dict[str, Any] = {
        "nome": "Ana Souza",
        "email": "ana@exemplo.com",
        "telefone": "(11) 98765-4321",
        "cargo": "Desenvolvedora",
        "senha": "segredo123",
    }
    dados.update(alteracoes)
    return dados


def test_cria_conta_e_ja_entra(client: TestClient) -> None:
    resposta = client.post(URL, json=dados_validos())

    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["nome"] == "Ana Souza"
    assert corpo["email"] == "ana@exemplo.com"
    assert corpo["telefone"] == "11987654321"
    assert corpo["cargo"] == "Desenvolvedora"
    assert corpo["data_nascimento"] is None
    assert corpo["troca_senha_obrigatoria"] is False
    assert "sessao" in resposta.cookies
    assert client.get("/api/v1/me").json()["id"] == corpo["id"]


def test_cookie_de_sessao_e_http_only(client: TestClient) -> None:
    resposta = client.post(URL, json=dados_validos())
    cookie = resposta.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "samesite=lax" in cookie


def test_cria_conta_com_data_de_nascimento(client: TestClient) -> None:
    resposta = client.post(URL, json=dados_validos(data_nascimento="1995-03-15"))
    assert resposta.status_code == 201
    assert resposta.json()["data_nascimento"] == "1995-03-15"


@pytest.mark.parametrize("campo", ["nome", "email", "telefone", "cargo", "senha"])
def test_campo_obrigatorio_faltando(client: TestClient, campo: str) -> None:
    dados = dados_validos()
    del dados[campo]

    resposta = client.post(URL, json=dados)

    assert resposta.status_code == 422
    erro = resposta.json()["erro"]
    assert erro["codigo"] == "validacao"
    assert campo in erro["campos"]


def test_indica_todos_os_campos_que_faltam(client: TestClient) -> None:
    resposta = client.post(URL, json={})
    assert set(resposta.json()["erro"]["campos"]) >= {"nome", "email", "telefone", "cargo", "senha"}


@pytest.mark.parametrize("campo", ["nome", "cargo"])
def test_texto_so_com_espacos_conta_como_vazio(client: TestClient, campo: str) -> None:
    resposta = client.post(URL, json=dados_validos(**{campo: "   "}))
    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_email_repetido_com_outra_grafia(client: TestClient) -> None:
    client.post(URL, json=dados_validos())

    resposta = client.post(URL, json=dados_validos(email=" ANA@Exemplo.com "))

    assert resposta.status_code == 409
    assert resposta.json()["erro"]["codigo"] == "email_ja_cadastrado"


def test_email_ja_gravado_por_outra_requisicao(
    client: TestClient, criar_usuario: Callable[..., Usuario]
) -> None:
    # Simula a corrida: a conta já existe quando o cadastro grava.
    criar_usuario(email="ana@exemplo.com")
    resposta = client.post(URL, json=dados_validos())
    assert resposta.status_code == 409


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("email", "ana@"),
        ("telefone", "123"),
        ("senha", "abcdefgh"),
        ("senha", "abc1234"),
        ("data_nascimento", "2026-09-29"),
        ("data_nascimento", "1899-12-31"),
        ("data_nascimento", "nao-e-data"),
        ("nome", "x" * 121),
        ("cargo", "x" * 81),
    ],
)
def test_valor_invalido(client: TestClient, campo: str, valor: str) -> None:
    resposta = client.post(URL, json=dados_validos(**{campo: valor}))

    assert resposta.status_code == 422
    assert campo in resposta.json()["erro"]["campos"]


def test_cadastro_publico_nao_aceita_papel(client: TestClient, db: Session) -> None:
    resposta = client.post(URL, json=dados_validos(papel="admin"))

    assert resposta.status_code == 422
    assert "papel" in resposta.json()["erro"]["campos"]
    assert db.scalar(select(Usuario).where(Usuario.papel == "admin")) is None


def test_conta_criada_e_de_usuario_comum(client: TestClient, db: Session) -> None:
    usuario_id = client.post(URL, json=dados_validos()).json()["id"]
    assert db.get(Usuario, usuario_id).papel == "usuario"


def test_cria_as_categorias_iniciais(client: TestClient, db: Session) -> None:
    usuario_id = client.post(URL, json=dados_validos()).json()["id"]

    categorias = db.scalars(select(Categoria).where(Categoria.usuario_id == usuario_id)).all()

    assert sorted((c.nome, c.tipo, c.sistema, c.ativa) for c in categorias) == sorted(
        [
            ("Salário", "entrada", True, True),
            ("Renda extra", "entrada", False, True),
            ("Moradia", "saida", False, True),
            ("Alimentação", "saida", False, True),
            ("Transporte", "saida", False, True),
            ("Saúde", "saida", False, True),
            ("Lazer", "saida", False, True),
            ("Outros", "saida", False, True),
            ("Poupança", "saida", True, True),
        ]
    )


def test_senha_guardada_so_como_hash(client: TestClient, db: Session) -> None:
    usuario_id = client.post(URL, json=dados_validos()).json()["id"]
    senha_hash = db.get(Usuario, usuario_id).senha_hash
    assert "segredo123" not in senha_hash
    assert senha_hash.startswith("$argon2id$")


def test_respostas_nunca_expoem_senha(client: TestClient) -> None:
    respostas = [
        client.post(URL, json=dados_validos()),
        client.get("/api/v1/me"),
        client.post(URL, json=dados_validos()),  # 409
        client.post(URL, json=dados_validos(email="b@exemplo.com", senha="curta")),  # 422
    ]
    for resposta in respostas:
        texto = resposta.text
        assert "senha_hash" not in texto
        assert "segredo123" not in texto
        assert "argon2" not in texto


def test_respostas_mostram_so_o_proprio_papel(client: TestClient) -> None:
    """O papel aparece para o frontend separar a área do admin; nunca é aceito na entrada."""
    assert client.post(URL, json=dados_validos()).json()["papel"] == "usuario"
    assert client.get("/api/v1/me").json()["papel"] == "usuario"
