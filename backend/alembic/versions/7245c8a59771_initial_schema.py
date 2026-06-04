"""initial_schema

Revision ID: 7245c8a59771
Revises:
Create Date: 2026-06-03 15:52:12.390618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7245c8a59771"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("full_name", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "campus_signals",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("location_name", sa.String(length=200), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("priority", sa.String(length=50), nullable=False),
        sa.Column("department", sa.String(length=100), nullable=True),
        sa.Column("suggested_department", sa.String(length=100), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=False),
        sa.Column("assigned_staff_id", sa.Integer(), nullable=True),
        sa.Column("supervisor_id", sa.Integer(), nullable=True),
        sa.Column("resolution_note", sa.Text(), nullable=True),
        sa.Column("supervisor_note", sa.Text(), nullable=True),
        sa.Column("reopen_count", sa.Integer(), nullable=False),
        sa.Column("reopen_reason", sa.Text(), nullable=True),
        sa.Column("ai_category", sa.String(length=100), nullable=True),
        sa.Column("ai_sentiment", sa.String(length=50), nullable=True),
        sa.Column("ai_priority", sa.String(length=50), nullable=True),
        sa.Column("ai_summary", sa.Text(), nullable=True),
        sa.Column("duplicate_score", sa.Float(), nullable=False),
        sa.Column("hotspot_score", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_campus_signals_id"), "campus_signals", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_campus_signals_id"), table_name="campus_signals")
    op.drop_table("campus_signals")

    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_index(op.f("ix_users_id"), table_name="users")
    op.drop_table("users")