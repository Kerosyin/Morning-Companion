"""add access grants

Revision ID: d4e5f6071829
Revises: c3d4e5f60718
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

from app.config import get_settings

revision: str = "d4e5f6071829"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f60718"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "access_grants",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("granted_by", sa.BigInteger(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("telegram_id"),
    )
    op.create_index("ix_access_grants_telegram_id", "access_grants", ["telegram_id"])

    settings = get_settings()
    grants = sorted(set(settings.allowed_users) - {settings.admin_id})
    if grants:
        access_grants = sa.table(
            "access_grants",
            sa.column("telegram_id", sa.BigInteger()),
            sa.column("granted_by", sa.BigInteger()),
        )
        op.bulk_insert(
            access_grants,
            [
                {"telegram_id": telegram_id, "granted_by": settings.admin_id}
                for telegram_id in grants
            ],
        )


def downgrade() -> None:
    op.drop_index("ix_access_grants_telegram_id", table_name="access_grants")
    op.drop_table("access_grants")
