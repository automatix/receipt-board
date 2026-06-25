"""FastAPI dependencies: per-request transactional session, audit context, services, token.

One SQLite transaction per request (ADR-0008): the session commits when the endpoint
returns successfully and rolls back on any error. Origin is derived from the request — a
valid session token means GUI, an explicit CLI marker means CLI, otherwise REST.
"""

from __future__ import annotations

import secrets
from collections.abc import Iterator

from fastapi import Depends, Request
from sqlalchemy.orm import Session

from receipt_board.api.errors import ApiError
from receipt_board.core.audit import ORIGIN_CLI, ORIGIN_GUI, ORIGIN_REST, AuditService
from receipt_board.core.services import ChecklistService, VocabularyService

CLIENT_HEADER = "X-Receipt-Board-Client"
TOKEN_HEADER = "X-Session-Token"
SESSION_ID_HEADER = "X-Session-Id"


def get_session(request: Request) -> Iterator[Session]:
    session = request.app.state.session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def _token_is_valid(request: Request) -> bool:
    token = request.headers.get(TOKEN_HEADER)
    expected = request.app.state.session_token
    return bool(token) and secrets.compare_digest(token, expected)


def detect_origin(request: Request) -> str:
    if _token_is_valid(request):
        return ORIGIN_GUI
    if request.headers.get(CLIENT_HEADER, "").lower() == "cli":
        return ORIGIN_CLI
    return ORIGIN_REST


def get_audit(request: Request, session: Session = Depends(get_session)) -> AuditService:
    return AuditService(
        session,
        origin=detect_origin(request),
        session_id=request.headers.get(SESSION_ID_HEADER),
        app_version=request.app.state.app_version,
    )


def get_checklist_service(
    session: Session = Depends(get_session), audit: AuditService = Depends(get_audit)
) -> ChecklistService:
    return ChecklistService(session, audit)


def get_vocab_service(
    session: Session = Depends(get_session), audit: AuditService = Depends(get_audit)
) -> VocabularyService:
    return VocabularyService(session, audit)


def require_token(request: Request) -> None:
    token = request.headers.get(TOKEN_HEADER)
    if not token:
        raise ApiError(401, "missing_token", "A session token is required for this operation")
    if not _token_is_valid(request):
        raise ApiError(403, "invalid_token", "Invalid session token")
