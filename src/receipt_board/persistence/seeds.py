"""Controlled-vocabulary seed values (TECH_SPEC §3).

These are inserted by the initial migration so every fresh DB at ``head`` already
carries them; the helper is also reused by tests that build the schema directly.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from receipt_board.persistence.models import ResourceType, Tool

RESOURCE_TYPE_SEEDS: tuple[dict, ...] = (
    {"name": "URL", "value_optional": False, "value_pattern": r"^https?://"},
    {"name": "Email", "value_optional": True, "value_pattern": r"^[^@\s]+@[^@\s]+\.[^@\s]+$"},
)
TOOL_SEEDS: tuple[str, ...] = ("Browser", "Thunderbird")


def seed_vocabularies(session: Session) -> None:
    """Insert the seed vocabularies if missing (idempotent on the unique ``name``)."""
    existing_types = set(session.scalars(select(ResourceType.name)).all())
    for seed in RESOURCE_TYPE_SEEDS:
        if seed["name"] not in existing_types:
            session.add(ResourceType(**seed))

    existing_tools = set(session.scalars(select(Tool.name)).all())
    for name in TOOL_SEEDS:
        if name not in existing_tools:
            session.add(Tool(name=name))
    session.flush()
