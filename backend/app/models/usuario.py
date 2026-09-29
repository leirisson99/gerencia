from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Identity,
    Index,
    String,
    false,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

PAPEL_USUARIO = "usuario"
PAPEL_ADMIN = "admin"
INDICE_ADMIN_UNICO = "uq_usuario_admin_unico"


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("papel IN ('usuario', 'admin')", name="papel"),
        # Um único administrador por enquanto; remover o índice libera vários.
        Index(INDICE_ADMIN_UNICO, "papel", unique=True, postgresql_where=text("papel = 'admin'")),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True)
    senha_hash: Mapped[str] = mapped_column(String(255))
    telefone: Mapped[str] = mapped_column(String(11))
    cargo: Mapped[str] = mapped_column(String(80))
    data_nascimento: Mapped[date | None]
    papel: Mapped[str] = mapped_column(
        String(10), default=PAPEL_USUARIO, server_default=PAPEL_USUARIO
    )
    troca_senha_obrigatoria: Mapped[bool] = mapped_column(default=False, server_default=false())
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
