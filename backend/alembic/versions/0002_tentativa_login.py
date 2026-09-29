"""tentativa_login

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-28
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tentativa_login",
        sa.Column("id", sa.BigInteger(), sa.Identity(), nullable=False),
        sa.Column("email_normalizado", sa.String(254), nullable=False),
        sa.Column("ocorrida_em", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_tentativa_login"),
    )
    op.create_index(
        "ix_tentativa_login_email_ocorrida",
        "tentativa_login",
        ["email_normalizado", "ocorrida_em"],
    )


def downgrade() -> None:
    op.drop_index("ix_tentativa_login_email_ocorrida", table_name="tentativa_login")
    op.drop_table("tentativa_login")
