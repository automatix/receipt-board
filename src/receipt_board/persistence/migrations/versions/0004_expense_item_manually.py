"""expense-item manually flag

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-15

Adds the boolean ``manually`` to ``expense_items`` (issue #156): the whole entry cannot
be automated / must be handled manually. Import/export notation: a ``~manually~`` marker
outside the bracket groups (e.g. ``- [ ] Taxi ~manually~``). Defaults to false for all
existing rows.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004"
down_revision: str | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "expense_items",
        sa.Column("manually", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )


def downgrade() -> None:
    with op.batch_alter_table("expense_items") as batch:
        batch.drop_column("manually")
