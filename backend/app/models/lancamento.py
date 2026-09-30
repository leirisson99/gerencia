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
    select,
    text,
    true,
)
from sqlalchemy.orm import Mapped, column_property, mapped_column, relationship

from app.domain.usuario import ciclo_pelo_mes
from app.models import Base
from app.models.cartela import Casa
from app.models.categoria import Categoria
from app.models.servico import Servico
from app.models.usuario import Usuario

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
        Index("ix_lancamento_recorrencia_data", "recorrencia_id", "data"),
        CheckConstraint("(divida_id IS NULL) = (parcela_num IS NULL)", name="parcela"),
        UniqueConstraint("divida_id", "parcela_num", name="uq_lancamento_divida_parcela"),
        # A mesma movimentação de extrato não é importada duas vezes pelo mesmo usuário.
        Index(
            "uq_lancamento_usuario_id_externo",
            "usuario_id",
            "id_externo",
            unique=True,
            postgresql_where=text("id_externo IS NOT NULL"),
        ),
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
    recorrencia_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("recorrencia.id", ondelete="RESTRICT")
    )
    divida_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("divida.id", ondelete="RESTRICT")
    )
    parcela_num: Mapped[int | None] = mapped_column(SmallInteger)
    id_externo: Mapped[str | None] = mapped_column(String(120))  # só em importados
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    categoria: Mapped[Categoria] = relationship()

    # Depósito de cartela: vem na mesma consulta, para o frontend travar o que a API recusa.
    cartela_id: Mapped[int | None] = column_property(
        select(Casa.cartela_id)
        .where(Casa.lancamento_id == id)
        .correlate_except(Casa)
        .scalar_subquery()
    )

    # Serviço a receber que gerou esta entrada (feature 013), ou None.
    servico_id: Mapped[int | None] = column_property(
        select(Servico.id)
        .where(Servico.lancamento_id == id)
        .correlate_except(Servico)
        .scalar_subquery()
    )

    # Tipo de renda do dono: para o prestador, "Salário" não abre ciclo.
    tipo_renda_usuario: Mapped[str] = column_property(
        select(Usuario.tipo_renda)
        .where(Usuario.id == usuario_id)
        .correlate_except(Usuario)
        .scalar_subquery()
    )

    @property
    def importado(self) -> bool:
        return self.id_externo is not None

    @property
    def abre_ciclo(self) -> bool:
        return (
            self.categoria.e_salario
            and self.status == STATUS_REALIZADO
            and not ciclo_pelo_mes(self.tipo_renda_usuario)
        )
