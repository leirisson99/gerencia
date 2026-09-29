from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    ForeignKey,
    Identity,
    Index,
    String,
    false,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.categoria import e_categoria_salario
from app.models import Base

INDICE_NOME_UNICO = "uq_categoria_usuario_nome"


class Categoria(Base):
    __tablename__ = "categoria"
    __table_args__ = (
        CheckConstraint("tipo IN ('entrada', 'saida')", name="tipo"),
        CheckConstraint("limite > 0", name="limite_positivo"),
        Index(
            "uq_categoria_salario_sistema",
            "usuario_id",
            unique=True,
            postgresql_where=text("sistema AND nome = 'Salário'"),
        ),
        # Nome único por usuário, sem diferenciar maiúsculas.
        Index(INDICE_NOME_UNICO, "usuario_id", func.lower(text("nome")), unique=True),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    nome: Mapped[str] = mapped_column(String(60))
    tipo: Mapped[str] = mapped_column(String(7))
    ativa: Mapped[bool] = mapped_column(default=True, server_default=true())
    sistema: Mapped[bool] = mapped_column(default=False, server_default=false())
    # Gasto máximo por ciclo, em centavos; só em categoria de saída (domain/limite.py).
    limite: Mapped[int | None] = mapped_column(BigInteger)

    @property
    def e_salario(self) -> bool:
        return e_categoria_salario(self.nome, self.sistema)
