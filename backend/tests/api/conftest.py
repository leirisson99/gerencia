"""Fixtures da área do administrador."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models import Usuario
from app.schemas.admin import DadosAdmin
from app.services.admin import criar_administrador
from tests.conftest import RelogioFixo

USUARIOS = "/api/v1/admin/usuarios"


@pytest.fixture
def admin(db: Session, relogio: RelogioFixo) -> Usuario:
    usuario, _ = criar_administrador(
        db,
        DadosAdmin(nome="Admin", email="admin@exemplo.com", telefone="11987654321", cargo="Adm"),
        relogio.agora,
    )
    # Troca inicial já feita, para os testes irem direto às rotas.
    db.execute(
        update(Usuario).where(Usuario.id == usuario.id).values(troca_senha_obrigatoria=False)
    )
    db.commit()
    return usuario


@pytest.fixture
def cliente_admin(
    client: TestClient, admin: Usuario, logar: Callable[[TestClient, Usuario], str]
) -> TestClient:
    logar(client, admin)
    return client


@pytest.fixture
def usuarios(criar_usuario: Callable[..., Usuario], relogio: RelogioFixo) -> dict[str, Usuario]:
    caio = criar_usuario(email="caio@exemplo.com", nome="Caio Dias")
    relogio.avancar(minutes=1)
    ana = criar_usuario(email="ana@exemplo.com", nome="Ana Souza", cargo="Dev")
    bia = criar_usuario(email="bia@exemplo.com", nome="Bia Lima")
    return {"ana": ana, "bia": bia, "caio": caio}
