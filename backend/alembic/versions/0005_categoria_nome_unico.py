"""nome de categoria único por usuário

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: str | None = "0004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index(
        "uq_categoria_usuario_nome",
        "categoria",
        ["usuario_id", sa.text("lower(nome)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_categoria_usuario_nome", table_name="categoria")
