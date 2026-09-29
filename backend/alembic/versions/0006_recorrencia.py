"""recorrencia e lancamento.recorrencia_id

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006"
down_revision: str | None = "0005"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "recorrencia",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("categoria_id", sa.BigInteger(), nullable=False),
        sa.Column("descricao", sa.String(200), nullable=False),
        sa.Column("valor", sa.BigInteger(), nullable=False),
        sa.Column("tipo", sa.String(7), nullable=False),
        sa.Column("dia", sa.SmallInteger(), nullable=False),
        sa.Column("ativa", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("valor > 0", name="ck_recorrencia_valor_positivo"),
        sa.CheckConstraint("tipo IN ('entrada', 'saida')", name="ck_recorrencia_tipo"),
        sa.CheckConstraint("dia BETWEEN 1 AND 31", name="ck_recorrencia_dia"),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name="fk_recorrencia_usuario_id_usuario",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categoria.id"],
            name="fk_recorrencia_categoria_id_categoria",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_recorrencia"),
    )
    op.create_index("ix_recorrencia_usuario_id", "recorrencia", ["usuario_id"])

    op.add_column("lancamento", sa.Column("recorrencia_id", sa.BigInteger(), nullable=True))
    op.create_foreign_key(
        "fk_lancamento_recorrencia_id_recorrencia",
        "lancamento",
        "recorrencia",
        ["recorrencia_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index("ix_lancamento_recorrencia_data", "lancamento", ["recorrencia_id", "data"])


def downgrade() -> None:
    op.drop_index("ix_lancamento_recorrencia_data", table_name="lancamento")
    op.drop_constraint("fk_lancamento_recorrencia_id_recorrencia", "lancamento", type_="foreignkey")
    op.drop_column("lancamento", "recorrencia_id")
    op.drop_index("ix_recorrencia_usuario_id", table_name="recorrencia")
    op.drop_table("recorrencia")
