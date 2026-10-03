from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, ForeignKey, Identity, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

ACAO_RESET_SENHA = "reset_senha"
ACAO_DESATIVAR_CONTA = "desativar_conta"
ACAO_REATIVAR_CONTA = "reativar_conta"
ACAO_VER_ATIVIDADE = "ver_atividade"


class AcaoAdmin(Base):
    """Auditoria de toda ação administrativa."""

    __tablename__ = "acao_admin"
    __table_args__ = (
        CheckConstraint(
            "acao IN ('reset_senha', 'desativar_conta', 'reativar_conta', 'ver_atividade')",
            name="acao",
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    admin_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"))
    acao: Mapped[str] = mapped_column(String(30))
    usuario_alvo_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    ocorrida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
