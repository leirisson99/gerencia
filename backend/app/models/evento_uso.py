from datetime import datetime
from typing import Literal, get_args

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

TipoEvento = Literal[
    "conta_criada",
    "login",
    "senha_trocada",
    "perfil_atualizado",
    "lancamento_criado",
    "lancamento_editado",
    "lancamento_excluido",
    "extrato_importado",
    "categoria_criada",
    "categoria_editada",
    "recorrencia_criada",
    "recorrencia_editada",
    "divida_criada",
    "cartela_criada",
    "deposito_feito",
    "deposito_desfeito",
    "servico_criado",
    "servico_editado",
    "servico_excluido",
    "servico_recebido",
    "recebimento_desfeito",
    "lembrete_criado",
    "lembrete_editado",
    "lembrete_concluido",
    "lembrete_excluido",
    "push_ativado",
    "push_removido",
]
TIPOS_EVENTO: tuple[str, ...] = get_args(TipoEvento)


class EventoUso(Base):
    """Uso de uma conta, sem conteúdo: só quem, o quê (tipo) e quando.

    Nunca guarde aqui valores, descrições, nomes ou o id do registro afetado
    (constituição 6.0.0, princípio V).
    """

    __tablename__ = "evento_uso"
    __table_args__ = (
        CheckConstraint(f"tipo IN ({', '.join(repr(t) for t in TIPOS_EVENTO)})", name="tipo"),
        Index("ix_evento_uso_usuario_id_id", "usuario_id", "id"),
        Index("ix_evento_uso_ocorrido_em", "ocorrido_em"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE")
    )
    tipo: Mapped[str] = mapped_column(String(30))
    ocorrido_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
