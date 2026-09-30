from datetime import date, datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class Servico(Base):
    """Serviço prestado a um cliente, ligado à entrada (lançamento) que ele gera.

    A situação (a receber, atrasado, recebido) é derivada do lançamento (domain/servico.py).
    """

    __tablename__ = "servico"
    __table_args__ = (CheckConstraint("valor > 0", name="valor_positivo"),)

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categoria.id", ondelete="RESTRICT")
    )
    cliente: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str | None] = mapped_column(String(200))
    valor: Mapped[int] = mapped_column(BigInteger)  # centavos, o combinado
    data_prevista: Mapped[date]
    lancamento_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("lancamento.id", ondelete="RESTRICT"), unique=True
    )
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
