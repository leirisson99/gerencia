"""Problemas na configuração do admin não derrubam a API: só desligam o admin, com aviso."""

from collections.abc import Callable
from contextlib import nullcontext

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.config import Settings
from app.db import get_db
from app.main import create_app
from app.models import Usuario


def subir(settings: Settings, db: Session) -> TestClient:
    aplicacao = create_app(settings)
    aplicacao.dependency_overrides[get_db] = lambda: db
    return TestClient(aplicacao)


def test_hash_invalido_sobe_a_api_e_avisa(
    settings_teste: Settings, db: Session, caplog: pytest.LogCaptureFixture
) -> None:
    settings = settings_teste.model_copy(
        update={"admin_email": "root@exemplo.com", "admin_senha_hash": "naoehash"}
    )

    with caplog.at_level("WARNING"), subir(settings, db) as cliente:
        assert cliente.get("/health").status_code == 200

    assert "Administrador do .env desligado" in caplog.text
    assert "naoehash" not in caplog.text


def test_email_de_usuario_comum_sobe_a_api_e_avisa(
    settings_teste: Settings,
    db: Session,
    criar_usuario: Callable[..., Usuario],
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from app import main
    from app.services.senha import hash_senha

    criar_usuario(email="root@exemplo.com")
    db.commit()
    # A inicialização abre a própria sessão; aqui ela usa a do teste.
    monkeypatch.setattr(main, "SessionLocal", lambda: nullcontext(db))
    settings = settings_teste.model_copy(
        update={"admin_email": "root@exemplo.com", "admin_senha_hash": hash_senha("segredo1")}
    )

    with caplog.at_level("WARNING"), subir(settings, db) as cliente:
        assert cliente.get("/health").status_code == 200

    assert "Administrador do .env desligado" in caplog.text
    assert "conta de usuário" in caplog.text
