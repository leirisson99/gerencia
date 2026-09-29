"""usuario, sessao e categoria

Revision ID: 0001
Revises:
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "usuario",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("nome", sa.String(120), nullable=False),
        sa.Column("email", sa.String(254), nullable=False),
        sa.Column("senha_hash", sa.String(255), nullable=False),
        sa.Column("telefone", sa.String(11), nullable=False),
        sa.Column("cargo", sa.String(80), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("papel", sa.String(10), server_default="usuario", nullable=False),
        sa.Column(
            "troca_senha_obrigatoria", sa.Boolean(), server_default=sa.false(), nullable=False
        ),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("papel IN ('usuario', 'admin')", name="ck_usuario_papel"),
        sa.PrimaryKeyConstraint("id", name="pk_usuario"),
        sa.UniqueConstraint("email", name="uq_usuario_email"),
    )

    op.create_table(
        "sessao",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("token_hash", sa.CHAR(64), nullable=False),
        sa.Column(
            "criada_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "ultimo_uso_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name="fk_sessao_usuario_id_usuario",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_sessao"),
        sa.UniqueConstraint("token_hash", name="uq_sessao_token_hash"),
    )
    op.create_index("ix_sessao_usuario_id", "sessao", ["usuario_id"])

    op.create_table(
        "categoria",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.String(60), nullable=False),
        sa.Column("tipo", sa.String(7), nullable=False),
        sa.Column("ativa", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sistema", sa.Boolean(), server_default=sa.false(), nullable=False),
        sa.CheckConstraint("tipo IN ('entrada', 'saida')", name="ck_categoria_tipo"),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name="fk_categoria_usuario_id_usuario",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_categoria"),
    )
    op.create_index("ix_categoria_usuario_id", "categoria", ["usuario_id"])
    op.create_index(
        "uq_categoria_salario_sistema",
        "categoria",
        ["usuario_id"],
        unique=True,
        postgresql_where=sa.text("sistema AND nome = 'Salário'"),
    )


def downgrade() -> None:
    op.drop_index("uq_categoria_salario_sistema", table_name="categoria")
    op.drop_index("ix_categoria_usuario_id", table_name="categoria")
    op.drop_table("categoria")
    op.drop_index("ix_sessao_usuario_id", table_name="sessao")
    op.drop_table("sessao")
    op.drop_table("usuario")
