"""Fixtures da área do administrador."""

from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Usuario
from app.schemas.admin import DadosAdmin
from app.services.admin import sincronizar_administrador
from app.services.senha import hash_senha
from tests.conftest import RelogioFixo

USUARIOS = "/api/v1/admin/usuarios"


@pytest.fixture
def admin(db: Session, relogio: RelogioFixo) -> Usuario:
    """O administrador como a inicialização o cria a partir do .env."""
    dados = DadosAdmin(
        nome="Admin", email="admin@exemplo.com", senha_hash=hash_senha("segredoAdmin1")
    )
    sincronizar_administrador(db, dados, relogio.agora)
    return db.scalars(select(Usuario).where(Usuario.papel == "admin")).one()


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
