"""In-app updater endpoints (issue #81, ADR-0013).

GUI-only feature → token-gated (the whole router carries the session-token dependency).
``GET /update/check`` reports whether a newer public GitHub Release exists.
"""

from __future__ import annotations

import httpx
from fastapi import APIRouter, Depends, Request

from receipt_board.api.deps import require_token
from receipt_board.api.errors import ApiError
from receipt_board.api.schemas import UpdateCheckResponse
from receipt_board.core import updates

update_router = APIRouter(tags=["update"], dependencies=[Depends(require_token)])


@update_router.get("/update/check", response_model=UpdateCheckResponse)
def check_update(request: Request) -> dict:
    """Compare the running version against the latest public release."""
    current = request.app.state.app_version
    try:
        with httpx.Client(timeout=updates.REQUEST_TIMEOUT) as client:
            info = updates.check_for_update(current, client=client)
    except httpx.HTTPError as exc:
        raise ApiError(502, "update_check_failed", "Could not reach the update server") from exc
    return info.as_dict()
