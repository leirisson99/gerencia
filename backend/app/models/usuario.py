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
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.domain.usuario import TIPO_CLT
from app.models import Base

PAPEL_USUARIO = "usuario"
PAPEL_ADMIN = "admin"
INDICE_ADMIN_UNICO = "uq_usuario_admin_unico"


class Usuario(Base):
    __tablename__ = "usuario"
    __table_args__ = (
        CheckConstraint("papel IN ('usuario', 'admin')", name="papel"),
        CheckConstraint("tipo_renda IN ('clt', 'prestador', 'clt_prestador')", name="tipo_renda"),
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
    # Define a regra do ciclo (domain/usuario.py: ciclo_pelo_mes).
    tipo_renda: Mapped[str] = mapped_column(String(13), default=TIPO_CLT, server_default=TIPO_CLT)
    troca_senha_obrigatoria: Mapped[bool] = mapped_column(default=False, server_default=false())
    # Conta desativada pelo administrador: não entra, mas mantém os dados.
    ativo: Mapped[bool] = mapped_column(default=True, server_default=true())
    # Carteira PJ ligada ("Tenho CNPJ"); só para prestador e clt_prestador.
    tem_pj: Mapped[bool] = mapped_column(default=False, server_default=false())
    # Só para contar contas ativas no painel do admin; gravado no máximo uma vez por dia.
    ultimo_acesso_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
