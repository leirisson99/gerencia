from datetime import datetime

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.domain.atividade import limite_retencao
from app.models import EventoUso
from app.models.evento_uso import TipoEvento


def registrar(db: Session, usuario_id: int, tipo: TipoEvento) -> None:
    """Anota o uso na transação da ação: se a ação falhar, o evento some junto."""
    db.add(EventoUso(usuario_id=usuario_id, tipo=tipo))


def limpar_antigos(db: Session, agora: datetime) -> int:
    """Apaga os eventos com mais de 12 meses e devolve quantos saíram."""
    resultado = db.execute(delete(EventoUso).where(EventoUso.ocorrido_em < limite_retencao(agora)))
    db.commit()
    return resultado.rowcount
