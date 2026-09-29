from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    SmallInteger,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

DEVO = "devo"
ME_DEVEM = "me_devem"
CARTAO = "cartao"


class Divida(Base):
    """Algo que devo ou que me devem, pago em parcelas (lançamentos previstos)."""

    __tablename__ = "divida"
    __table_args__ = (
        CheckConstraint("direcao IN ('devo', 'me_devem')", name="direcao"),
        CheckConstraint(
            "forma_pagamento IN ('pix', 'boleto', 'cartao', 'dinheiro')", name="forma_pagamento"
        ),
        CheckConstraint("parcelas BETWEEN 1 AND 120", name="parcelas"),
        CheckConstraint("valor_total >= parcelas", name="valor_total"),
        CheckConstraint("dia_vencimento BETWEEN 1 AND 31", name="dia_vencimento"),
        CheckConstraint("NOT (forma_pagamento = 'cartao' AND direcao = 'me_devem')", name="cartao"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    usuario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categoria.id", ondelete="RESTRICT")
    )
    descricao: Mapped[str] = mapped_column(String(200))
    pessoa: Mapped[str] = mapped_column(String(120))
    direcao: Mapped[str] = mapped_column(String(9))
    valor_total: Mapped[int] = mapped_column(BigInteger)  # centavos
    parcelas: Mapped[int] = mapped_column(SmallInteger)
    forma_pagamento: Mapped[str] = mapped_column(String(8))
    dia_vencimento: Mapped[int] = mapped_column(SmallInteger)
    data_inicio: Mapped[date]
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
