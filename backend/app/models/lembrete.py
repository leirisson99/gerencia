from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, ForeignKey, Identity, Index, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Lembrete(Base):
    """Lembrete livre do usuário (texto e data).

    Contas a pagar e valores a receber não têm tabela: são derivados dos previstos
    (domain/lembrete.py).
    """

    __tablename__ = "lembrete"
    __table_args__ = (Index("ix_lembrete_usuario_data", "usuario_id", "data"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE")
    )
    texto: Mapped[str] = mapped_column(String(200))
    data: Mapped[date]
    concluido_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    @property
    def concluido(self) -> bool:
        return self.concluido_em is not None


class InscricaoPush(Base):
    """Aparelho autorizado a receber o resumo. O endpoint identifica o aparelho e é único."""

    __tablename__ = "inscricao_push"

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    endpoint: Mapped[str] = mapped_column(Text, unique=True)
    p256dh: Mapped[str] = mapped_column(String(200))
    auth: Mapped[str] = mapped_column(String(100))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EnvioLembrete(Base):
    """Resumo de um dia já entregue a um usuário: no máximo um por dia."""

    __tablename__ = "envio_lembrete"

    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), primary_key=True
    )
    dia: Mapped[date] = mapped_column(Date, primary_key=True)
    enviado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
