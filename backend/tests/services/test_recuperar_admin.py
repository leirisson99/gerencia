from collections.abc import Callable

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.erros import ErroApi
from app.models import AcaoAdmin, Sessao, Usuario
from app.schemas.admin import DadosAdmin
from app.services.admin import criar_administrador, resetar_senha_do_administrador
from app.services.senha import hash_senha, verificar_senha
from app.services.sessao import criar_sessao
from tests.conftest import SENHA_PADRAO, RelogioFixo


@pytest.fixture
def admin(db: Session, relogio: RelogioFixo) -> Usuario:
    """Administrador que já trocou a senha e perdeu o acesso."""
    usuario, _ = criar_administrador(
        db,
        DadosAdmin(nome="Admin", email="admin@exemplo.com", telefone="11987654321", cargo="Adm"),
        relogio.agora,
    )
    usuario.senha_hash = hash_senha("esquecida123")
    usuario.troca_senha_obrigatoria = False
    db.commit()
    return usuario


def sessoes(db: Session, usuario: Usuario) -> int:
    return db.scalar(
        select(func.count()).select_from(Sessao).where(Sessao.usuario_id == usuario.id)
    )


def test_gera_senha_nova_e_a_antiga_deixa_de_valer(
    db: Session, relogio: RelogioFixo, admin: Usuario
) -> None:
    senha = resetar_senha_do_administrador(db, relogio.agora)

    db.refresh(admin)
    assert verificar_senha(admin.senha_hash, senha)
    assert not verificar_senha(admin.senha_hash, "esquecida123")


def test_exige_troca_no_proximo_login(db: Session, relogio: RelogioFixo, admin: Usuario) -> None:
    resetar_senha_do_administrador(db, relogio.agora)

    db.refresh(admin)
    assert admin.troca_senha_obrigatoria is True


def test_derruba_as_sessoes_do_admin_e_preserva_as_dos_usuarios(
    db: Session,
    relogio: RelogioFixo,
    admin: Usuario,
    criar_usuario: Callable[..., Usuario],
) -> None:
    ana = criar_usuario()
    criar_sessao(db, admin, relogio.agora)
    criar_sessao(db, ana, relogio.agora)
    db.commit()

    resetar_senha_do_administrador(db, relogio.agora)

    assert sessoes(db, admin) == 0
    assert sessoes(db, ana) == 1


def test_nao_altera_contas_de_usuario_comum(
    db: Session,
    relogio: RelogioFixo,
    admin: Usuario,
    criar_usuario: Callable[..., Usuario],
) -> None:
    ana = criar_usuario()
    db.commit()

    resetar_senha_do_administrador(db, relogio.agora)

    db.refresh(ana)
    assert verificar_senha(ana.senha_hash, SENHA_PADRAO)
    assert ana.troca_senha_obrigatoria is False


def test_operacao_de_servidor_nao_entra_no_registro_de_acoes(
    db: Session, relogio: RelogioFixo, admin: Usuario
) -> None:
    resetar_senha_do_administrador(db, relogio.agora)

    assert db.scalar(select(func.count()).select_from(AcaoAdmin)) == 0


def test_sem_administrador_cadastrado(db: Session, relogio: RelogioFixo) -> None:
    with pytest.raises(ErroApi) as erro:
        resetar_senha_do_administrador(db, relogio.agora)

    assert erro.value.codigo == "nao_encontrado"
