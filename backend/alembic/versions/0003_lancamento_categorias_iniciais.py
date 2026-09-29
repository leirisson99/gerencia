"""lancamento e categorias iniciais

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Cópia literal de app.domain.categoria.CATEGORIAS_INICIAIS: a migração não depende do código.
CATEGORIAS_INICIAIS = [
    ("Salário", "entrada", True),
    ("Renda extra", "entrada", False),
    ("Moradia", "saida", False),
    ("Alimentação", "saida", False),
    ("Transporte", "saida", False),
    ("Saúde", "saida", False),
    ("Lazer", "saida", False),
    ("Outros", "saida", False),
]


def upgrade() -> None:
    op.create_table(
        "lancamento",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("categoria_id", sa.BigInteger(), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("valor", sa.BigInteger(), nullable=False),
        sa.Column("tipo", sa.String(7), nullable=False),
        sa.Column("descricao", sa.String(200), nullable=True),
        sa.Column("status", sa.String(9), server_default="realizado", nullable=False),
        sa.Column("conta_no_saldo", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "atualizado_em",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint("valor > 0", name="ck_lancamento_valor_positivo"),
        sa.CheckConstraint("tipo IN ('entrada', 'saida')", name="ck_lancamento_tipo"),
        sa.CheckConstraint("status IN ('previsto', 'realizado')", name="ck_lancamento_status"),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuario.id"],
            name="fk_lancamento_usuario_id_usuario",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categoria.id"],
            name="fk_lancamento_categoria_id_categoria",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_lancamento"),
    )
    op.create_index("ix_lancamento_usuario_data", "lancamento", ["usuario_id", "data"])
    op.create_index(
        "ix_lancamento_usuario_categoria_data",
        "lancamento",
        ["usuario_id", "categoria_id", "data"],
    )

    # Usuários já cadastrados recebem as categorias iniciais que ainda não têm.
    for nome, tipo, sistema in CATEGORIAS_INICIAIS:
        op.execute(
            sa.text(
                """
                INSERT INTO categoria (usuario_id, nome, tipo, sistema)
                SELECT u.id, :nome, :tipo, :sistema
                FROM usuario u
                WHERE NOT EXISTS (
                    SELECT 1 FROM categoria c WHERE c.usuario_id = u.id AND c.nome = :nome
                )
                """
            ).bindparams(nome=nome, tipo=tipo, sistema=sistema)
        )


def downgrade() -> None:
    op.drop_index("ix_lancamento_usuario_categoria_data", table_name="lancamento")
    op.drop_index("ix_lancamento_usuario_data", table_name="lancamento")
    op.drop_table("lancamento")
    nomes = [nome for nome, _, sistema in CATEGORIAS_INICIAIS if not sistema]
    op.execute(
        sa.text("DELETE FROM categoria WHERE NOT sistema AND nome IN :nomes").bindparams(
            sa.bindparam("nomes", value=nomes, expanding=True)
        )
    )
