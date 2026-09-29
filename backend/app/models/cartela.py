from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Cartela(Base):
    """Meta de poupança sem prazo, dividida em casas."""

    __tablename__ = "cartela"
    __table_args__ = (
        CheckConstraint("meta > 0", name="meta_positiva"),
        CheckConstraint("valor_base > 0 AND valor_base <= meta", name="valor_base"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(80))
    meta: Mapped[int] = mapped_column(BigInteger)  # centavos
    valor_base: Mapped[int] = mapped_column(BigInteger)  # centavos
    criada_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Casa(Base):
    """Um depósito da cartela; livre enquanto `depositado_em` for nulo."""

    __tablename__ = "casa"
    __table_args__ = (
        CheckConstraint("valor > 0", name="valor_positivo"),
        CheckConstraint("(depositado_em IS NULL) = (lancamento_id IS NULL)", name="deposito"),
        UniqueConstraint("cartela_id", "ordem", name="uq_casa_cartela_ordem"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    cartela_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cartela.id", ondelete="CASCADE")
    )
    valor: Mapped[int] = mapped_column(BigInteger)  # centavos
    ordem: Mapped[int] = mapped_column(SmallInteger)
    is_ajuste: Mapped[bool]
    depositado_em: Mapped[date | None]
    lancamento_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("lancamento.id", ondelete="RESTRICT"), unique=True
    )
