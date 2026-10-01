"""lembretes livres e push

Revision ID: 0015
Revises: 0014
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0015"
down_revision: str | None = "0014"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _criado_em(nome: str = "criado_em") -> sa.Column:
    return sa.Column(nome, sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)


def upgrade() -> None:
    op.create_table(
        "lembrete",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("texto", sa.String(200), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("concluido_em", sa.DateTime(timezone=True), nullable=True),
        _criado_em(),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name="fk_lembrete_usuario_id_usuario",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_lembrete"),
    )
    op.create_index("ix_lembrete_usuario_data", "lembrete", ["usuario_id", "data"])

    op.create_table(
        "inscricao_push",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("endpoint", sa.Text(), nullable=False),
        sa.Column("p256dh", sa.String(200), nullable=False),
        sa.Column("auth", sa.String(100), nullable=False),
        _criado_em(),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name="fk_inscricao_push_usuario_id_usuario",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_inscricao_push"),
        sa.UniqueConstraint("endpoint", name="uq_inscricao_push_endpoint"),
    )
    op.create_index("ix_inscricao_push_usuario_id", "inscricao_push", ["usuario_id"])

    op.create_table(
        "envio_lembrete",
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("dia", sa.Date(), nullable=False),
        _criado_em("enviado_em"),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name="fk_envio_lembrete_usuario_id_usuario",
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("usuario_id", "dia", name="pk_envio_lembrete"),
    )


def downgrade() -> None:
    op.drop_table("envio_lembrete")
    op.drop_index("ix_inscricao_push_usuario_id", table_name="inscricao_push")
    op.drop_table("inscricao_push")
    op.drop_index("ix_lembrete_usuario_data", table_name="lembrete")
    op.drop_table("lembrete")
