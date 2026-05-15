add usage_logs table

Revision ID: 004
Revises: 003
Create Date: 2026-05-15

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usage_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("session_id", postgresql.UUID(as_uuid=True)),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100)),
        sa.Column("input_tokens", sa.Integer, nullable=False),
        sa.Column("output_tokens", sa.Integer, nullable=False),
        sa.Column("total_tokens", sa.Integer, nullable=False),
        sa.Column("cached_tokens", sa.Integer, server_default="0"),
        sa.Column("reasoning_tokens", sa.Integer, server_default="0"),
        sa.Column("requests", sa.Integer, server_default="0"),
        sa.Column("duration_ms", sa.Integer),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_usage_logs_agent_id", "usage_logs", ["agent_id"])
    op.create_index("idx_usage_logs_created_at", "usage_logs", ["created_at"])


def downgrade() -> None:
    op.drop_index("idx_usage_logs_created_at")
    op.drop_index("idx_usage_logs_agent_id")
    op.drop_table("usage_logs")
