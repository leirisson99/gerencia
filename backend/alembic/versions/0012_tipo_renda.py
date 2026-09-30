"""tipo de renda do usuário

Revision ID: 0012
Revises: 0011
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0012"
down_revision: str | None = "0011"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Contas existentes viram "clt": o ciclo continua aberto pelo salário.
    op.add_column(
        "usuario",
        sa.Column("tipo_renda", sa.String(13), nullable=False, server_default="clt"),
    )
    op.create_check_constraint(
        "tipo_renda", "usuario", "tipo_renda IN ('clt', 'prestador', 'clt_prestador')"
    )


def downgrade() -> None:
    op.drop_constraint("tipo_renda", "usuario", type_="check")
    op.drop_column("usuario", "tipo_renda")
