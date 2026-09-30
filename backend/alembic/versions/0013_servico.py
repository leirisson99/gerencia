"""serviço a receber

Revision ID: 0013
Revises: 0012
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0013"
down_revision: str | None = "0012"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "servico",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("categoria_id", sa.BigInteger(), nullable=False),
        sa.Column("cliente", sa.String(120), nullable=False),
        sa.Column("descricao", sa.String(200), nullable=True),
        sa.Column("valor", sa.BigInteger(), nullable=False),
        sa.Column("data_prevista", sa.Date(), nullable=False),
        sa.Column("lancamento_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("valor > 0", name="ck_servico_valor_positivo"),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name="fk_servico_usuario_id_usuario", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categoria.id"],
            name="fk_servico_categoria_id_categoria",
            ondelete="RESTRICT",
        ),
        sa.ForeignKeyConstraint(
            ["lancamento_id"],
            ["lancamento.id"],
            name="fk_servico_lancamento_id_lancamento",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_servico"),
        sa.UniqueConstraint("lancamento_id", name="uq_servico_lancamento_id"),
    )
    op.create_index("ix_servico_usuario_id", "servico", ["usuario_id"])


def downgrade() -> None:
    op.drop_index("ix_servico_usuario_id", table_name="servico")
    op.drop_table("servico")
