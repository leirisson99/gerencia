from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    String,
    func,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models import Base
from app.models.categoria import Categoria

STATUS_PREVISTO = "previsto"
STATUS_REALIZADO = "realizado"


class Lancamento(Base):
    __tablename__ = "lancamento"
    __table_args__ = (
        CheckConstraint("valor > 0", name="valor_positivo"),
        CheckConstraint("tipo IN ('entrada', 'saida')", name="tipo"),
        CheckConstraint("status IN ('previsto', 'realizado')", name="status"),
        Index("ix_lancamento_usuario_data", "usuario_id", "data"),
        Index("ix_lancamento_usuario_categoria_data", "usuario_id", "categoria_id", "data"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE")
    )
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categoria.id", ondelete="RESTRICT")
    )
    data: Mapped[date]
    valor: Mapped[int] = mapped_column(BigInteger)  # centavos
    tipo: Mapped[str] = mapped_column(String(7))  # copiado da categoria
    descricao: Mapped[str | None] = mapped_column(String(200))
    status: Mapped[str] = mapped_column(
        String(9), default=STATUS_REALIZADO, server_default=STATUS_REALIZADO
    )
    conta_no_saldo: Mapped[bool] = mapped_column(default=True, server_default=true())
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    categoria: Mapped[Categoria] = relationship()

    @property
    def abre_ciclo(self) -> bool:
        return self.categoria.e_salario and self.status == STATUS_REALIZADO
