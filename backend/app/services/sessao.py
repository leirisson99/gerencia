import hashlib
import secrets
from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.domain.login import sessao_expirada
from app.models import Sessao, Usuario


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def criar_sessao(db: Session, usuario: Usuario, agora: datetime) -> str:
    """Cria a sessão e devolve o token em claro; só o hash fica no banco."""
    token = secrets.token_urlsafe(32)
    db.add(
        Sessao(
            usuario_id=usuario.id,
            token_hash=_hash_token(token),
            criada_em=agora,
            ultimo_uso_em=agora,
        )
    )
    db.flush()
    return token


def resolver_sessao(db: Session, token: str, agora: datetime, dias: int) -> Sessao | None:
    sessao = db.scalar(select(Sessao).where(Sessao.token_hash == _hash_token(token)))
    if sessao is None:
        return None
    if sessao_expirada(sessao.ultimo_uso_em, agora, dias):
        db.delete(sessao)
        db.commit()
        return None
    sessao.ultimo_uso_em = agora
    db.commit()
    return sessao


def encerrar_sessao(db: Session, sessao: Sessao) -> None:
    db.delete(sessao)
    db.flush()


def encerrar_outras_sessoes(db: Session, usuario_id: int, sessao_atual_id: int) -> None:
    db.execute(delete(Sessao).where(Sessao.usuario_id == usuario_id, Sessao.id != sessao_atual_id))
