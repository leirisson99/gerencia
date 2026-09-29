"""acao_admin e administrador único

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_usuario_admin_unico",
        "usuario",
        ["papel"],
        unique=True,
        postgresql_where=sa.text("papel = 'admin'"),
    )
    op.create_table(
        "acao_admin",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("admin_id", sa.BigInteger(), nullable=False),
        sa.Column("acao", sa.String(30), nullable=False),
        sa.Column("usuario_alvo_id", sa.BigInteger(), nullable=False),
        sa.Column("ocorrida_em", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("acao IN ('reset_senha')", name="ck_acao_admin_acao"),
        sa.ForeignKeyConstraint(
            ["admin_id"],
            ["usuario.id"],
            name="fk_acao_admin_admin_id_usuario",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_alvo_id"],
            ["usuario.id"],
            name="fk_acao_admin_usuario_alvo_id_usuario",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_acao_admin"),
    )
    op.create_index("ix_acao_admin_usuario_alvo_id", "acao_admin", ["usuario_alvo_id"])


def downgrade() -> None:
    op.drop_index("ix_acao_admin_usuario_alvo_id", table_name="acao_admin")
    op.drop_table("acao_admin")
    op.drop_index("uq_usuario_admin_unico", table_name="usuario")
