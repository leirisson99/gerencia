from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.db import get_db
from app.main import create_app
from app.models import Categoria, Usuario
from app.relogio import Relogio, get_relogio
from app.services.senha import hash_senha
from app.services.sessao import criar_sessao

SENHA_PADRAO = "segredo123"


def _url_teste() -> str:
    url = get_settings().test_database_url
    if not url:
        raise RuntimeError("Defina TEST_DATABASE_URL (veja .env.example).")
    return url


class RelogioFixo(Relogio):
    def __init__(self, agora: datetime) -> None:
        self.agora = agora

    def agora_utc(self) -> datetime:
        return self.agora

    def avancar(self, **delta: float) -> None:
        self.agora += timedelta(**delta)


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    url = _url_teste()
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", url)
    command.downgrade(cfg, "base")
    command.upgrade(cfg, "head")
    eng = create_engine(url)
    yield eng
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    """Cada teste roda numa transação desfeita ao final."""
    conexao = engine.connect()
    transacao = conexao.begin()
    sessao = Session(
        bind=conexao,
        join_transaction_mode="create_savepoint",
        autoflush=False,
        expire_on_commit=False,
    )
    yield sessao
    sessao.close()
    transacao.rollback()
    conexao.close()


@pytest.fixture
def relogio() -> RelogioFixo:
    # 12h em São Paulo
    return RelogioFixo(datetime(2026, 9, 28, 15, 0, tzinfo=UTC))


@pytest.fixture
def settings_teste() -> Settings:
    url = _url_teste()
    return Settings(
        database_url=url,
        test_database_url=url,
        frontend_origin="http://localhost:3000",
        cookie_secure=False,
        # O admin do .env de desenvolvimento não entra nos testes.
        admin_email=None,
        admin_senha_hash=None,
    )


@pytest.fixture
def app(db: Session, relogio: RelogioFixo, settings_teste: Settings) -> FastAPI:
    aplicacao = create_app(settings_teste)
    aplicacao.dependency_overrides[get_db] = lambda: db
    aplicacao.dependency_overrides[get_relogio] = lambda: relogio
    aplicacao.dependency_overrides[get_settings] = lambda: settings_teste
    return aplicacao


@pytest.fixture
def client(app: FastAPI) -> Iterator[TestClient]:
    with TestClient(app) as cliente:
        yield cliente


@pytest.fixture
def novo_client(app: FastAPI) -> Iterator[Callable[[], TestClient]]:
    """Clientes extras, cada um com seus cookies (outro navegador)."""
    abertos: list[TestClient] = []

    def _novo() -> TestClient:
        cliente = TestClient(app)
        abertos.append(cliente)
        return cliente

    yield _novo
    for cliente in abertos:
        cliente.close()


@pytest.fixture
def criar_usuario(db: Session, relogio: RelogioFixo) -> Callable[..., Usuario]:
    """Cria o usuário direto no banco, sem depender do cadastro."""

    def _criar(email: str = "ana@exemplo.com", senha: str = SENHA_PADRAO, **campos: Any) -> Usuario:
        dados: dict[str, Any] = {
            "nome": "Ana Souza",
            "telefone": "11987654321",
            "cargo": "Desenvolvedora",
            "criado_em": relogio.agora,
            "atualizado_em": relogio.agora,
        }
        dados.update(campos)
        usuario = Usuario(email=email, senha_hash=hash_senha(senha), **dados)
        db.add(usuario)
        db.flush()
        return usuario

    return _criar


@pytest.fixture
def logar(db: Session, relogio: RelogioFixo) -> Callable[[TestClient, Usuario], str]:
    """Abre uma sessão para o usuário e coloca o cookie no cliente."""

    def _logar(cliente: TestClient, usuario: Usuario) -> str:
        token = criar_sessao(db, usuario, relogio.agora)
        db.commit()
        cliente.cookies.set("sessao", token)
        return token

    return _logar


@dataclass
class Conta:
    usuario: Usuario
    categorias: dict[str, int]  # nome → id


@pytest.fixture
def criar_conta(
    db: Session,
    criar_usuario: Callable[..., Usuario],
    logar: Callable[[TestClient, Usuario], str],
) -> Callable[..., Conta]:
    """Usuário logado no cliente, com as categorias iniciais do cadastro."""
    from app.services.categoria import criar_categorias_iniciais

    def _criar(cliente: TestClient, email: str = "ana@exemplo.com") -> Conta:
        usuario = criar_usuario(email=email)
        criar_categorias_iniciais(db, usuario.id)
        db.flush()
        logar(cliente, usuario)
        categorias = db.scalars(select(Categoria).where(Categoria.usuario_id == usuario.id))
        return Conta(usuario=usuario, categorias={c.nome: c.id for c in categorias})

    return _criar
