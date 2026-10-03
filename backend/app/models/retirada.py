from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Retirada(Base):
    """Dinheiro da PJ para a PF (pró-labore e lucros). Dona dos dois lançamentos que a
    representam: só muda ou some junto com eles (constituição 7.0.0, princípio I)."""

    __tablename__ = "retirada"
    __table_args__ = (CheckConstraint("valor > 0", name="valor_positivo"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    data: Mapped[date]
    valor: Mapped[int] = mapped_column(BigInteger)  # centavos
    descricao: Mapped[str | None] = mapped_column(String(200))
    lancamento_pj_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lancamento.id", ondelete="RESTRICT"), unique=True
    )
    lancamento_pf_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lancamento.id", ondelete="RESTRICT"), unique=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
