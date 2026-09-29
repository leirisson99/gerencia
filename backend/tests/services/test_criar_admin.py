from collections.abc import Callable

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.erros import ErroApi
from app.models import Categoria, Usuario
from app.schemas.admin import DadosAdmin
from app.services.admin import criar_administrador
from app.services.senha import verificar_senha
from tests.conftest import RelogioFixo


def dados(**alteracoes: str) -> DadosAdmin:
    valores = {
        "nome": "Admin",
        "email": " ADMIN@Exemplo.com ",
        "telefone": "(11) 98765-4321",
        "cargo": "Administrador",
    }
    valores.update(alteracoes)
    return DadosAdmin(**valores)


def test_cria_o_administrador_com_senha_temporaria(db: Session, relogio: RelogioFixo) -> None:
    admin, senha = criar_administrador(db, dados(), relogio.agora)

    assert admin.papel == "admin"
    assert admin.email == "admin@exemplo.com"
    assert admin.telefone == "11987654321"
    assert admin.troca_senha_obrigatoria is True
    assert verificar_senha(admin.senha_hash, senha)


def test_administrador_nao_recebe_categorias(db: Session, relogio: RelogioFixo) -> None:
    admin, _ = criar_administrador(db, dados(), relogio.agora)
    total = db.scalar(
        select(func.count()).select_from(Categoria).where(Categoria.usuario_id == admin.id)
    )
    assert total == 0


def test_so_existe_um_administrador(db: Session, relogio: RelogioFixo) -> None:
    criar_administrador(db, dados(), relogio.agora)

    with pytest.raises(ErroApi) as erro:
        criar_administrador(db, dados(email="outro@exemplo.com"), relogio.agora)

    assert erro.value.codigo == "administrador_existente"
    total = db.scalar(select(func.count()).select_from(Usuario).where(Usuario.papel == "admin"))
    assert total == 1


def test_email_ja_cadastrado(
    db: Session, relogio: RelogioFixo, criar_usuario: Callable[..., Usuario]
) -> None:
    criar_usuario(email="admin@exemplo.com")

    with pytest.raises(ErroApi) as erro:
        criar_administrador(db, dados(), relogio.agora)

    assert erro.value.codigo == "email_ja_cadastrado"


@pytest.mark.parametrize(
    ("campo", "valor"), [("email", "admin@"), ("telefone", "123"), ("nome", "  "), ("cargo", "")]
)
def test_dados_invalidos(campo: str, valor: str) -> None:
    with pytest.raises(ValidationError):
        dados(**{campo: valor})
