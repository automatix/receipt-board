"""resource-type value metadata (value_optional, value_pattern)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-26

Adds per-type metadata to ``resource_types`` so resource notation becomes data-driven
(issues #43/#44): whether a value is optional and a regex the value must match. Backfills
the seeded URL/Email types; values match receipt_board.persistence.seeds.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_URL_PATTERN = r"^https?://"
_EMAIL_PATTERN = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


def upgrade() -> None:
    op.add_column(
        "resource_types",
        sa.Column("value_optional", sa.Boolean(), nullable=False, server_default=sa.text("0")),
    )
    op.add_column("resource_types", sa.Column("value_pattern", sa.String(), nullable=True))

    resource_types = sa.table(
        "resource_types",
        sa.column("name", sa.String),
        sa.column("value_optional", sa.Boolean),
        sa.column("value_pattern", sa.String),
    )
    op.execute(
        resource_types.update()
        .where(resource_types.c.name == "URL")
        .values(value_optional=False, value_pattern=_URL_PATTERN)
    )
    op.execute(
        resource_types.update()
        .where(resource_types.c.name == "Email")
        .values(value_optional=True, value_pattern=_EMAIL_PATTERN)
    )


def downgrade() -> None:
    with op.batch_alter_table("resource_types") as batch:
        batch.drop_column("value_pattern")
        batch.drop_column("value_optional")
