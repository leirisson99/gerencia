from datetime import datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    SmallInteger,
    String,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Recorrencia(Base):
    """Gasto ou renda fixa que gera um lançamento previsto por ciclo."""

    __tablename__ = "recorrencia"
    __table_args__ = (
        CheckConstraint("valor > 0", name="valor_positivo"),
        CheckConstraint("tipo IN ('entrada', 'saida')", name="tipo"),
        CheckConstraint("dia BETWEEN 1 AND 31", name="dia"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categoria.id", ondelete="RESTRICT")
    )
    descricao: Mapped[str] = mapped_column(String(200))
    valor: Mapped[int] = mapped_column(BigInteger)  # centavos
    tipo: Mapped[str] = mapped_column(String(7))  # copiado da categoria
    dia: Mapped[int] = mapped_column(SmallInteger)
    ativa: Mapped[bool] = mapped_column(default=True, server_default=true())
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
