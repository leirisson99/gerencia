from datetime import date, datetime

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Identity,
    Index,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
    text,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models import Base

PENDENTE = "pendente"
ACEITO = "aceito"
RECUSADO = "recusado"
REMOVIDO = "removido"
SAIU = "saiu"


class ContaCompartilhada(Base):
    """Conta mensal (aluguel, água, luz) dividida entre usuários do app (constituição 8.1.0).

    Quem pode ver: o dono e os participantes `aceito`. Só o dono edita."""

    __tablename__ = "conta_compartilhada"
    __table_args__ = (
        CheckConstraint("modo IN ('igual', 'percentual', 'fixo')", name="modo"),
        CheckConstraint("dia_vencimento BETWEEN 1 AND 31", name="dia_vencimento"),
        CheckConstraint("valor_fixo IS NULL OR valor_fixo > 0", name="valor_fixo"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    dono_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE"), index=True
    )
    categoria_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("categoria.id", ondelete="RESTRICT")
    )
    descricao: Mapped[str] = mapped_column(String(200))
    modo: Mapped[str] = mapped_column(String(10))
    dia_vencimento: Mapped[int] = mapped_column(SmallInteger)
    valor_fixo: Mapped[int | None] = mapped_column(BigInteger)  # centavos; nulo = informar por mês
    ativa: Mapped[bool] = mapped_column(default=True, server_default=true())
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ParticipanteConta(Base):
    """O dono (`eh_dono`) ou um convidado por e-mail. `usuario_id` fica nulo até o convidado
    aceitar ou se cadastrar com aquele e-mail."""

    __tablename__ = "participante_conta"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pendente', 'aceito', 'recusado', 'removido', 'saiu')", name="status"
        ),
        CheckConstraint("valor IS NULL OR valor >= 0", name="valor"),
        CheckConstraint("eh_dono OR email_convite IS NOT NULL", name="convite"),
        UniqueConstraint("conta_id", "usuario_id", name="uq_participante_conta_conta_usuario"),
        UniqueConstraint("conta_id", "email_convite", name="uq_participante_conta_conta_email"),
        Index(
            "uq_participante_conta_dono",
            "conta_id",
            unique=True,
            postgresql_where=text("eh_dono"),
        ),
        Index("ix_participante_conta_usuario_id", "usuario_id"),
        Index(
            "ix_participante_conta_email_pendente",
            "email_convite",
            postgresql_where=text("status = 'pendente'"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    conta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conta_compartilhada.id", ondelete="CASCADE"), index=True
    )
    usuario_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("usuario.id", ondelete="CASCADE")
    )
    email_convite: Mapped[str | None] = mapped_column(String(254))  # minúsculas
    status: Mapped[str] = mapped_column(String(10), default=PENDENTE)
    categoria_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("categoria.id", ondelete="RESTRICT")
    )
    valor: Mapped[int | None] = mapped_column(BigInteger)  # bps (percentual) ou centavos (fixo)
    eh_dono: Mapped[bool] = mapped_column(default=False, server_default=text("false"))
    convidado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class CobrancaMensal(Base):
    """Total de uma conta numa competência (dia 1 do mês), dividido entre os aceitos na hora."""

    __tablename__ = "cobranca_mensal"
    __table_args__ = (
        CheckConstraint("valor_total > 0", name="valor_total"),
        UniqueConstraint("conta_id", "competencia", name="uq_cobranca_mensal_conta_competencia"),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    conta_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("conta_compartilhada.id", ondelete="CASCADE")
    )
    competencia: Mapped[date]
    valor_total: Mapped[int] = mapped_column(BigInteger)  # centavos
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CotaCobranca(Base):
    """Parte de um participante numa cobrança. Sem coluna de status: o status mostrado é
    derivado do lançamento do titular e de `confirmado_em` (`domain.status_da_cota`)."""

    __tablename__ = "cota_cobranca"
    __table_args__ = (
        CheckConstraint("valor > 0", name="valor_positivo"),
        UniqueConstraint(
            "cobranca_id", "participante_id", name="uq_cota_cobranca_cobranca_participante"
        ),
        Index(
            "ix_cota_cobranca_participante_sem_lancamento",
            "participante_id",
            postgresql_where=text("lancamento_id IS NULL"),
        ),
    )

    id: Mapped[int] = mapped_column(BigInteger, Identity(), primary_key=True)
    cobranca_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("cobranca_mensal.id", ondelete="CASCADE")
    )
    participante_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("participante_conta.id", ondelete="CASCADE")
    )
    valor: Mapped[int] = mapped_column(BigInteger)  # centavos
    # Só do usuário titular da cota; nulo até ele ler o ciclo (e enquanto não há ciclo).
    lancamento_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("lancamento.id", ondelete="RESTRICT"), unique=True
    )
    confirmado_em: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
