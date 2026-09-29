from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Identity, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base


class TentativaLogin(Base):
    """Uma falha de login. Sem FK: o e-mail pode não pertencer a nenhuma conta."""

    __tablename__ = "tentativa_login"
    __table_args__ = (
        Index("ix_tentativa_login_email_ocorrida", "email_normalizado", "ocorrida_em"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    email_normalizado: Mapped[str] = mapped_column(String(254))
    ocorrida_em: Mapped[datetime] = mapped_column(DateTime(timezone=True))
