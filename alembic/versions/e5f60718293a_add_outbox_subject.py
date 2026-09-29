"""Track the user described by an outbox notification.

Revision ID: e5f60718293a
Revises: d4e5f6071829
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e5f60718293a"
down_revision: Union[str, Sequence[str], None] = "d4e5f6071829"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "notification_outbox",
        sa.Column("subject_user_id", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_notification_outbox_subject_user_id",
        "notification_outbox",
        ["subject_user_id"],
    )

    connection = op.get_bind()
    rows = connection.execute(
        sa.text(
            "SELECT id, dedupe_key FROM notification_outbox "
            "WHERE kind = 'admin_inactive_user'"
        )
    )
    for row_id, dedupe_key in rows:
        _, separator, user_id = dedupe_key.rpartition(":")
        if separator and user_id.isdecimal():
            connection.execute(
                sa.text(
                    "UPDATE notification_outbox SET subject_user_id = :user_id "
                    "WHERE id = :row_id"
                ),
                {"user_id": int(user_id), "row_id": row_id},
            )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_outbox_subject_user_id",
        table_name="notification_outbox",
    )
    op.drop_column("notification_outbox", "subject_user_id")
