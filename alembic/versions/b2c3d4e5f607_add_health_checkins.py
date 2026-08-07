"""health check-ins

Revision ID: b2c3d4e5f607
Revises: a1b2c3d4e5f6
Create Date: 2026-08-07 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b2c3d4e5f607"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "daily_activities",
        sa.Column(
            "health_check_sent",
            sa.Boolean(),
            server_default="false",
            nullable=False,
        ),
    )
    op.create_table(
        "health_checkins",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("date", "user_id", name="uq_health_checkin_date_user"),
    )
    op.create_index(
        op.f("ix_health_checkins_user_id"),
        "health_checkins",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_health_checkins_date"), "health_checkins", ["date"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_health_checkins_date"), table_name="health_checkins")
    op.drop_index(op.f("ix_health_checkins_user_id"), table_name="health_checkins")
    op.drop_table("health_checkins")
    op.drop_column("daily_activities", "health_check_sent")