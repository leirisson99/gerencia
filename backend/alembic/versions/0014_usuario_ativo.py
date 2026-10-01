"""conta desativável pelo administrador

Revision ID: 0014
Revises: 0013
Create Date: 2026-09-30
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0014"
down_revision: str | None = "0013"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "usuario", sa.Column("ativo", sa.Boolean(), server_default=sa.true(), nullable=False)
    )
    op.drop_constraint("ck_acao_admin_acao", "acao_admin", type_="check")
    op.create_check_constraint(
        "ck_acao_admin_acao",
        "acao_admin",
        "acao IN ('reset_senha', 'desativar_conta', 'reativar_conta')",
    )


def downgrade() -> None:
    op.execute("DELETE FROM acao_admin WHERE acao <> 'reset_senha'")
    op.drop_constraint("ck_acao_admin_acao", "acao_admin", type_="check")
    op.create_check_constraint("ck_acao_admin_acao", "acao_admin", "acao IN ('reset_senha')")
    op.drop_column("usuario", "ativo")
