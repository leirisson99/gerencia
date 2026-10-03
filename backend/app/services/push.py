from sqlalchemy import delete
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.config import Settings
from app.erros import ErroApi
from app.models import InscricaoPush
from app.schemas.push import InscricaoIn
from app.services.evento_uso import registrar


def _indisponivel() -> ErroApi:
    return ErroApi(503, "push_indisponivel", "As notificações não estão disponíveis no momento.")


def push_configurado(settings: Settings) -> bool:
    return bool(
        settings.vapid_chave_publica and settings.vapid_chave_privada and settings.vapid_contato
    )


def chave_publica(settings: Settings) -> str:
    if not push_configurado(settings):
        raise _indisponivel()
    assert settings.vapid_chave_publica is not None
    return settings.vapid_chave_publica


def inscrever(db: Session, usuario_id: int, dados: InscricaoIn, settings: Settings) -> None:
    """Cria a inscrição do aparelho ou a passa para quem ativou: um aparelho, um usuário."""
    if not push_configurado(settings):
        raise _indisponivel()
    valores = {
        "usuario_id": usuario_id,
        "endpoint": dados.endpoint,
        "p256dh": dados.keys.p256dh,
        "auth": dados.keys.auth,
    }
    db.execute(
        insert(InscricaoPush)
        .values(**valores)
        .on_conflict_do_update(
            index_elements=[InscricaoPush.endpoint],
            set_={k: valores[k] for k in ("usuario_id", "p256dh", "auth")},
        )
    )
    registrar(db, usuario_id, "push_ativado")
    db.commit()


def remover_inscricao(db: Session, usuario_id: int, endpoint: str) -> None:
    """Desativa o aparelho. Funciona mesmo com o push desligado, para sair da conta limpar tudo."""
    removidas = db.execute(
        delete(InscricaoPush)
        .where(InscricaoPush.usuario_id == usuario_id, InscricaoPush.endpoint == endpoint)
        .returning(InscricaoPush.id)
    ).all()
    if not removidas:
        raise ErroApi(404, "nao_encontrado", "Aparelho não encontrado.")
    registrar(db, usuario_id, "push_removido")
    db.commit()
