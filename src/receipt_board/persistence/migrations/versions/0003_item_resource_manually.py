"""item-resource manually flag

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-15

Adds the boolean ``manually`` to ``item_resources`` (issue #135): the element cannot be
automated / must be handled manually. Import/export notation: a ``~manually~`` marker
inside the resource token. Defaults to false for all existing rows.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "item_resources",
        sa.Column("manually", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    with op.batch_alter_table("item_resources") as batch:
        batch.drop_column("manually")
