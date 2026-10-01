"""último acesso da conta, para o painel do administrador

Revision ID: 0016
Revises: 0015
Create Date: 2026-10-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0016"
down_revision: str | None = "0015"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("usuario", sa.Column("ultimo_acesso_em", sa.DateTime(timezone=True)))


def downgrade() -> None:
    op.drop_column("usuario", "ultimo_acesso_em")
