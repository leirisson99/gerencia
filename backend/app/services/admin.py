from datetime import datetime

from sqlalchemy import delete, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.erros import ErroApi
from app.models import AcaoAdmin, Sessao, Usuario
from app.models.acao_admin import ACAO_RESET_SENHA
from app.models.usuario import INDICE_ADMIN_UNICO, PAPEL_ADMIN, PAPEL_USUARIO
from app.schemas.admin import DadosAdmin
from app.services.senha import gerar_senha_temporaria, hash_senha


def _erro_admin_existente() -> ErroApi:
    return ErroApi(409, "administrador_existente", "Já existe um administrador.")


def criar_administrador(db: Session, dados: DadosAdmin, agora: datetime) -> tuple[Usuario, str]:
    """Cria o único administrador, com senha temporária e troca obrigatória no 1º login."""
    if db.scalar(select(Usuario.id).where(Usuario.papel == PAPEL_ADMIN)) is not None:
        raise _erro_admin_existente()

    senha = gerar_senha_temporaria()
    admin = Usuario(
        nome=dados.nome,
        email=dados.email,
        senha_hash=hash_senha(senha),
        telefone=dados.telefone,
        cargo=dados.cargo,
        papel=PAPEL_ADMIN,
        troca_senha_obrigatoria=True,
        criado_em=agora,
        atualizado_em=agora,
    )
    db.add(admin)
    try:
        db.flush()
    except IntegrityError as erro:
        db.rollback()
        # O índice único resolve dois comandos simultâneos.
        if INDICE_ADMIN_UNICO in str(erro.orig):
            raise _erro_admin_existente() from None
        raise ErroApi(409, "email_ja_cadastrado", "Este e-mail já está cadastrado.") from None
    db.commit()
    return admin, senha


def _escapar_like(texto: str) -> str:
    return texto.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def listar_usuarios(db: Session, busca: str | None) -> list[Usuario]:
    consulta = select(Usuario).where(Usuario.papel == PAPEL_USUARIO)
    if busca and busca.strip():
        padrao = f"%{_escapar_like(busca.strip())}%"
        consulta = consulta.where(
            or_(
                Usuario.nome.ilike(padrao, escape="\\"),
                Usuario.email.ilike(padrao, escape="\\"),
            )
        )
    return list(db.scalars(consulta.order_by(Usuario.nome, Usuario.id)))


def _aplicar_senha_temporaria(db: Session, usuario: Usuario, agora: datetime) -> str:
    """Troca a senha por uma temporária, derruba as sessões e exige troca no próximo login."""
    senha = gerar_senha_temporaria()
    usuario.senha_hash = hash_senha(senha)
    usuario.troca_senha_obrigatoria = True
    usuario.atualizado_em = agora
    db.execute(delete(Sessao).where(Sessao.usuario_id == usuario.id))
    return senha


def resetar_senha(db: Session, admin: Usuario, usuario_id: int, agora: datetime) -> str:
    """Gera senha temporária, derruba as sessões, exige troca e registra a ação."""
    usuario = db.scalar(
        select(Usuario).where(Usuario.id == usuario_id, Usuario.papel == PAPEL_USUARIO)
    )
    if usuario is None:
        raise ErroApi(404, "nao_encontrado", "Conta não encontrada.")

    senha = _aplicar_senha_temporaria(db, usuario, agora)
    db.add(
        AcaoAdmin(
            admin_id=admin.id,
            acao=ACAO_RESET_SENHA,
            usuario_alvo_id=usuario.id,
            ocorrida_em=agora,
        )
    )
    db.commit()
    return senha


def resetar_senha_do_administrador(db: Session, agora: datetime) -> str:
    """Recupera o acesso do administrador pelo servidor (comando `resetar-senha-admin`).

    Não entra no registro de ações: é operação de quem opera o servidor, não do painel.
    """
    admin = db.scalar(select(Usuario).where(Usuario.papel == PAPEL_ADMIN))
    if admin is None:
        raise ErroApi(404, "nao_encontrado", "Nenhum administrador cadastrado.")

    senha = _aplicar_senha_temporaria(db, admin, agora)
    db.commit()
    return senha
