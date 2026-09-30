"""importação de extrato: id_externo no lançamento

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-29
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010"
down_revision: str | None = "0009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("lancamento", sa.Column("id_externo", sa.String(120), nullable=True))
    op.create_index(
        "uq_lancamento_usuario_id_externo",
        "lancamento",
        ["usuario_id", "id_externo"],
        unique=True,
        postgresql_where=sa.text("id_externo IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index("uq_lancamento_usuario_id_externo", table_name="lancamento")
    op.drop_column("lancamento", "id_externo")
