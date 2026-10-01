"""Administrador sincronizado com o .env a cada inicialização: o .env sempre vence."""

from collections.abc import Callable

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings
from app.models import Categoria, Sessao, Usuario
from app.schemas.admin import DadosAdmin
from app.services.admin import sincronizar_administrador
from app.services.senha import hash_senha, verificar_senha
from app.services.sessao import criar_sessao
from tests.conftest import RelogioFixo

HASH = hash_senha("segredoAdmin1")


def dados(**alteracoes: str) -> DadosAdmin:
    valores = {"nome": "Admin", "email": " ADMIN@Exemplo.com ", "senha_hash": HASH}
    valores.update(alteracoes)
    return DadosAdmin(**valores)


def admins(db: Session) -> list[Usuario]:
    return list(db.scalars(select(Usuario).where(Usuario.papel == "admin")))


def sessoes(db: Session, usuario: Usuario) -> int:
    return db.scalar(
        select(func.count()).select_from(Sessao).where(Sessao.usuario_id == usuario.id)
    )


# --- Criação -------------------------------------------------------------------------------


def test_cria_o_administrador_com_a_senha_do_env(db: Session, relogio: RelogioFixo) -> None:
    assert sincronizar_administrador(db, dados(), relogio.agora) == "criado"

    [admin] = admins(db)
    assert admin.email == "admin@exemplo.com"
    assert admin.nome == "Admin"
    assert admin.troca_senha_obrigatoria is False
    assert admin.ativo is True
    assert verificar_senha(admin.senha_hash, "segredoAdmin1")


def test_administrador_nao_recebe_categorias(db: Session, relogio: RelogioFixo) -> None:
    sincronizar_administrador(db, dados(), relogio.agora)
    [admin] = admins(db)
    total = db.scalar(
        select(func.count()).select_from(Categoria).where(Categoria.usuario_id == admin.id)
    )
    assert total == 0


# --- Sincronização -------------------------------------------------------------------------


def test_sem_mudanca_nao_derruba_sessoes(db: Session, relogio: RelogioFixo) -> None:
    sincronizar_administrador(db, dados(), relogio.agora)
    [admin] = admins(db)
    criar_sessao(db, admin, relogio.agora)
    db.commit()

    assert sincronizar_administrador(db, dados(), relogio.agora) == "sem_mudanca"
    assert sessoes(db, admin) == 1


def test_nova_senha_no_env_vale_e_derruba_sessoes(db: Session, relogio: RelogioFixo) -> None:
    sincronizar_administrador(db, dados(), relogio.agora)
    [admin] = admins(db)
    criar_sessao(db, admin, relogio.agora)
    db.commit()

    resultado = sincronizar_administrador(
        db, dados(senha_hash=hash_senha("outraSenha2")), relogio.agora
    )

    assert resultado == "atualizado"
    assert admins(db) == [admin]
    assert verificar_senha(admin.senha_hash, "outraSenha2")
    assert not verificar_senha(admin.senha_hash, "segredoAdmin1")
    assert sessoes(db, admin) == 0


def test_novo_email_e_nome_no_env(db: Session, relogio: RelogioFixo) -> None:
    sincronizar_administrador(db, dados(), relogio.agora)
    [admin] = admins(db)
    criar_sessao(db, admin, relogio.agora)
    db.commit()

    sincronizar_administrador(db, dados(email="root@exemplo.com", nome="Root"), relogio.agora)

    assert (admin.email, admin.nome) == ("root@exemplo.com", "Root")
    assert sessoes(db, admin) == 0


def test_desfaz_alteracoes_feitas_fora_do_env(db: Session, relogio: RelogioFixo) -> None:
    sincronizar_administrador(db, dados(), relogio.agora)
    [admin] = admins(db)
    admin.senha_hash = hash_senha("mudadaNoBanco1")
    admin.troca_senha_obrigatoria = True
    admin.ativo = False
    db.commit()

    assert sincronizar_administrador(db, dados(), relogio.agora) == "atualizado"
    assert verificar_senha(admin.senha_hash, "segredoAdmin1")
    assert admin.troca_senha_obrigatoria is False
    assert admin.ativo is True


def test_email_de_usuario_comum_e_recusado(
    db: Session, relogio: RelogioFixo, criar_usuario: Callable[..., Usuario]
) -> None:
    criar_usuario(email="admin@exemplo.com")

    with pytest.raises(ValueError, match="já é usado por uma conta de usuário"):
        sincronizar_administrador(db, dados(), relogio.agora)
    assert admins(db) == []


# --- Configuração --------------------------------------------------------------------------


def config(**valores: str | None) -> Settings:
    return Settings(database_url="postgresql://x/y", _env_file=None, **valores)


def test_sem_admin_no_env() -> None:
    assert config().admin() is None


def test_admin_completo_no_env() -> None:
    admin = config(admin_email="Root@Exemplo.com", admin_senha_hash=HASH).admin()

    assert admin is not None
    assert (admin.email, admin.nome) == ("root@exemplo.com", "Administrador")


@pytest.mark.parametrize(
    "valores",
    [{"admin_email": "root@exemplo.com"}, {"admin_senha_hash": HASH}],
)
def test_email_e_hash_vem_juntos(valores: dict[str, str]) -> None:
    with pytest.raises(ValidationError, match="ADMIN_EMAIL e ADMIN_SENHA_HASH"):
        config(**valores)


@pytest.mark.parametrize("hash_invalido", ["segredoAdmin1", "$argon2id$quebrado"])
def test_hash_precisa_ser_argon2(hash_invalido: str) -> None:
    with pytest.raises(ValidationError, match="hash-senha"):
        config(admin_email="root@exemplo.com", admin_senha_hash=hash_invalido)
