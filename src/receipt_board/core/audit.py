"""Audit logging — one entry per caller action (ADR-0004, TECH_SPEC §8).

Constructed with the per-action context (``origin`` GUI/CLI/REST, optional
``session_id``). The entry is added in the same transaction as the mutation.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, datetime

from sqlalchemy.orm import Session

from receipt_board import __version__
from receipt_board.core.events import SESSION_DIRTY_KEY
from receipt_board.core.refs import NodeRef
from receipt_board.persistence.models import AuditEntry

ORIGIN_GUI = "GUI"
ORIGIN_CLI = "CLI"
ORIGIN_REST = "REST"


class AuditService:
    def __init__(
        self,
        session: Session,
        *,
        origin: str = ORIGIN_REST,
        session_id: str | None = None,
        app_version: str = __version__,
    ) -> None:
        self.session = session
        self.origin = origin
        self.session_id = session_id
        self.app_version = app_version

    def record(
        self,
        *,
        action_type: str,
        target_kind: str,
        target_id: int | None = None,
        checklist_id: int | None = None,
        payload: dict | None = None,
        affected: Iterable[NodeRef] | None = None,
    ) -> AuditEntry:
        entry = AuditEntry(
            ts=datetime.now(UTC).isoformat(),
            origin=self.origin,
            action_type=action_type,
            target_kind=target_kind,
            target_id=target_id,
            checklist_id=checklist_id,
            payload=payload,
            affected_ids=[ref.as_dict() for ref in (affected or [])],
            app_version=self.app_version,
            session_id=self.session_id,
        )
        self.session.add(entry)
        self.session.flush()
        # Flag the transaction as state-changing so the request scope publishes one change
        # event after it commits (live GUI refresh; see core.events / api.deps).
        self.session.info[SESSION_DIRTY_KEY] = True
        return entry
