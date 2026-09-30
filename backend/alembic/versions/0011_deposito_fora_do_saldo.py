"""depósito da cartela não conta no saldo

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-29
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0011"
down_revision: str | None = "0010"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "UPDATE lancamento SET conta_no_saldo = false "
        "WHERE id IN (SELECT lancamento_id FROM casa WHERE lancamento_id IS NOT NULL)"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE lancamento SET conta_no_saldo = true "
        "WHERE id IN (SELECT lancamento_id FROM casa WHERE lancamento_id IS NOT NULL)"
    )
