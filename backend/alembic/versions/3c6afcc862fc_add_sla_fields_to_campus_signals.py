"""add sla fields to campus signals

Revision ID: 3c6afcc862fc
Revises: b769a4a1a38e
Create Date: 2026-06-04 17:13:48.843296

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3c6afcc862fc"
down_revision: Union[str, Sequence[str], None] = "b769a4a1a38e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "campus_signals",
        sa.Column("sla_due_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "campus_signals",
        sa.Column(
            "sla_breached",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.add_column(
        "campus_signals",
        sa.Column("escalated_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("campus_signals", "escalated_at")
    op.drop_column("campus_signals", "sla_breached")
    op.drop_column("campus_signals", "sla_due_at")