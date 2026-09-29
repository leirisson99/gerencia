from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    String,
    false,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.categoria import e_categoria_salario
from app.models import Base


class Categoria(Base):
    __tablename__ = "categoria"
    __table_args__ = (
        CheckConstraint("tipo IN ('entrada', 'saida')", name="tipo"),
        Index(
            "uq_categoria_salario_sistema",
            "usuario_id",
            unique=True,
            postgresql_where=text("sistema AND nome = 'Salário'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(60))
    tipo: Mapped[str] = mapped_column(String(7))
    ativa: Mapped[bool] = mapped_column(default=True, server_default=true())
    sistema: Mapped[bool] = mapped_column(default=False, server_default=false())

    @property
    def e_salario(self) -> bool:
        return e_categoria_salario(self.nome, self.sistema)
