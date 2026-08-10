"""notification outbox

Revision ID: c3d4e5f60718
Revises: b2c3d4e5f607
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3d4e5f60718"
down_revision: Union[str, Sequence[str], None] = "b2c3d4e5f607"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "notification_outbox",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("kind", sa.String(length=50), nullable=False),
        sa.Column("dedupe_key", sa.String(length=200), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "sent",
                "failed",
                name="notification_status",
                native_enum=False,
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.Column("sent_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("kind", "dedupe_key", name="uq_notification_kind_dedupe"),
    )
    op.create_index(
        op.f("ix_notification_outbox_chat_id"),
        "notification_outbox",
        ["chat_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_outbox_kind"),
        "notification_outbox",
        ["kind"],
        unique=False,
    )
    op.create_index(
        op.f("ix_notification_outbox_status"),
        "notification_outbox",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(
        op.f("ix_notification_outbox_status"),
        table_name="notification_outbox",
    )
    op.drop_index(
        op.f("ix_notification_outbox_kind"),
        table_name="notification_outbox",
    )
    op.drop_index(
        op.f("ix_notification_outbox_chat_id"),
        table_name="notification_outbox",
    )
    op.drop_table("notification_outbox")
