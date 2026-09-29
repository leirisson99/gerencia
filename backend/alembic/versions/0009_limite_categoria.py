"""limite por categoria

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009"
down_revision: str | None = "0008"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("categoria", sa.Column("limite", sa.BigInteger(), nullable=True))
    op.create_check_constraint("limite_positivo", "categoria", "limite > 0")


def downgrade() -> None:
    op.drop_constraint("limite_positivo", "categoria", type_="check")
    op.drop_column("categoria", "limite")
