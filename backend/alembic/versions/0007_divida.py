"""divida e parcelas em lancamento

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: str | None = "0006"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "divida",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("usuario_id", sa.BigInteger(), nullable=False),
        sa.Column("categoria_id", sa.BigInteger(), nullable=False),
        sa.Column("descricao", sa.String(200), nullable=False),
        sa.Column("pessoa", sa.String(120), nullable=False),
        sa.Column("direcao", sa.String(9), nullable=False),
        sa.Column("valor_total", sa.BigInteger(), nullable=False),
        sa.Column("parcelas", sa.SmallInteger(), nullable=False),
        sa.Column("forma_pagamento", sa.String(8), nullable=False),
        sa.Column("dia_vencimento", sa.SmallInteger(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False),
        sa.Column(
            "criado_em", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("direcao IN ('devo', 'me_devem')", name="ck_divida_direcao"),
        sa.CheckConstraint(
            "forma_pagamento IN ('pix', 'boleto', 'cartao', 'dinheiro')",
            name="ck_divida_forma_pagamento",
        ),
        sa.CheckConstraint("parcelas BETWEEN 1 AND 120", name="ck_divida_parcelas"),
        sa.CheckConstraint("valor_total >= parcelas", name="ck_divida_valor_total"),
        sa.CheckConstraint("dia_vencimento BETWEEN 1 AND 31", name="ck_divida_dia_vencimento"),
        sa.CheckConstraint(
            "NOT (forma_pagamento = 'cartao' AND direcao = 'me_devem')", name="ck_divida_cartao"
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["usuario.id"], name="fk_divida_usuario_id_usuario", ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categoria.id"],
            name="fk_divida_categoria_id_categoria",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint("id", name="pk_divida"),
    )
    op.create_index("ix_divida_usuario_id", "divida", ["usuario_id"])

    op.add_column("lancamento", sa.Column("divida_id", sa.BigInteger(), nullable=True))
    op.add_column("lancamento", sa.Column("parcela_num", sa.SmallInteger(), nullable=True))
    op.create_foreign_key(
        "fk_lancamento_divida_id_divida",
        "lancamento",
        "divida",
        ["divida_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_check_constraint(
        "ck_lancamento_parcela", "lancamento", "(divida_id IS NULL) = (parcela_num IS NULL)"
    )
    op.create_unique_constraint(
        "uq_lancamento_divida_parcela", "lancamento", ["divida_id", "parcela_num"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_lancamento_divida_parcela", "lancamento", type_="unique")
    op.drop_constraint("ck_lancamento_parcela", "lancamento", type_="check")
    op.drop_constraint("fk_lancamento_divida_id_divida", "lancamento", type_="foreignkey")
    op.drop_column("lancamento", "parcela_num")
    op.drop_column("lancamento", "divida_id")
    op.drop_index("ix_divida_usuario_id", table_name="divida")
    op.drop_table("divida")
