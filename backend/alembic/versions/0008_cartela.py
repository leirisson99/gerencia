"""cartela, casa e categoria de sistema Poupança

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008"
down_revision: str | None = "0007"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "cartela",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("nome", sa.String(80), nullable=False),
        sa.Column("meta", sa.BigInteger(), nullable=False),
        sa.Column("valor_base", sa.BigInteger(), nullable=False),
        sa.Column(
            "criada_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("meta > 0", name="ck_cartela_meta_positiva"),
        sa.CheckConstraint("valor_base > 0 AND valor_base <= meta", name="ck_cartela_valor_base"),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name="fk_cartela_usuario_id_usuario", ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_cartela"),
    )
    op.create_index("ix_cartela_usuario_id", "cartela", ["usuario_id"])

    op.create_table(
        "casa",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("cartela_id", sa.BigInteger(), nullable=False),
        sa.Column("valor", sa.BigInteger(), nullable=False),
        sa.Column("ordem", sa.SmallInteger(), nullable=False),
        sa.Column("is_ajuste", sa.Boolean(), nullable=False),
        sa.Column("depositado_em", sa.Date(), nullable=True),
        sa.Column("lancamento_id", sa.BigInteger(), nullable=True),
        sa.CheckConstraint("valor > 0", name="ck_casa_valor_positivo"),
        sa.CheckConstraint(
            "(depositado_em IS NULL) = (lancamento_id IS NULL)", name="ck_casa_deposito"
        ),
        sa.ForeignKeyConstraint(
            ["cartela_id"], ["cartela.id"], name="fk_casa_cartela_id_cartela", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["lancamento_id"],
            ["lancamento.id"],
            name="fk_casa_lancamento_id_lancamento",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_casa"),
        sa.UniqueConstraint("cartela_id", "ordem", name="uq_casa_cartela_ordem"),
        sa.UniqueConstraint("lancamento_id", name="uq_casa_lancamento_id"),
    )

    # "Poupança" vira categoria do sistema para todos. Uma "Poupança" de saída criada à mão é
    # promovida; uma de entrada com esse nome é renomeada para liberar o nome.
    op.execute(
        "UPDATE categoria SET nome = 'Poupança (entrada)' "
        "WHERE lower(nome) = 'poupança' AND tipo = 'entrada'"
    )
    op.execute(
        "UPDATE categoria SET nome = 'Poupança', sistema = true, ativa = true "
        "WHERE lower(nome) = 'poupança' AND tipo = 'saida'"
    )
    op.execute(
        """
        INSERT INTO categoria (usuario_id, nome, tipo, sistema)
        SELECT u.id, 'Poupança', 'saida', true
        FROM usuario u
        WHERE u.papel = 'usuario' AND NOT EXISTS (
            SELECT 1 FROM categoria c WHERE c.usuario_id = u.id AND lower(c.nome) = 'poupança'
        )
        """
    )


def downgrade() -> None:
    # Mantém a categoria e os lançamentos; só deixa de ser do sistema.
    op.execute("UPDATE categoria SET sistema = false WHERE nome = 'Poupança' AND sistema")
    op.drop_table("casa")
    op.drop_index("ix_cartela_usuario_id", table_name="cartela")
    op.drop_table("cartela")
