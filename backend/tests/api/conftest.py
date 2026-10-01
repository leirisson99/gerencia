"""Fixtures da área do administrador."""

from collections.abc import Callable
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Categoria, Divida, Lancamento, Usuario
from app.schemas.admin import DadosAdmin
from app.services.admin import sincronizar_administrador
from app.services.categoria import criar_categorias_iniciais
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


@pytest.fixture
def lancar(db: Session) -> Callable[..., Lancamento]:
    """Grava lançamentos direto no banco, na primeira categoria do tipo pedido."""

    def _lancar(
        usuario: Usuario,
        tipo: str,
        data: date,
        status: str = "realizado",
        valor: int = 1_000,
        id_externo: str | None = None,
    ) -> Lancamento:
        if not db.scalar(select(Categoria.id).where(Categoria.usuario_id == usuario.id)):
            criar_categorias_iniciais(db, usuario.id)
            db.flush()
        categoria_id = db.scalar(
            select(Categoria.id)
            .where(Categoria.usuario_id == usuario.id, Categoria.tipo == tipo)
            .order_by(Categoria.id)
        )
        lancamento = Lancamento(
            usuario_id=usuario.id,
            categoria_id=categoria_id,
            data=data,
            valor=valor,
            tipo=tipo,
            status=status,
            id_externo=id_externo,
        )
        db.add(lancamento)
        db.flush()
        return lancamento

    return _lancar


@pytest.fixture
def endividar(db: Session, lancar: Callable[..., Lancamento]) -> Callable[[Usuario, str], None]:
    def _endividar(usuario: Usuario, forma: str) -> None:
        lancar(usuario, "saida", date(2026, 9, 1))  # garante as categorias
        categoria_id = db.scalar(
            select(Categoria.id).where(
                Categoria.usuario_id == usuario.id, Categoria.tipo == "saida"
            )
        )
        db.add(
            Divida(
                usuario_id=usuario.id,
                categoria_id=categoria_id,
                descricao="Notebook",
                pessoa="Loja",
                direcao="devo",
                valor_total=300_000,
                parcelas=3,
                forma_pagamento=forma,
                dia_vencimento=10,
                data_inicio=date(2026, 9, 10),
            )
        )
        db.flush()

    return _endividar
