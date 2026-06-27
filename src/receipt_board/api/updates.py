"""In-app updater endpoints (issues #81, #82; ADR-0013).

GUI-only feature → token-gated (the whole router carries the session-token dependency).
``GET /update/check`` reports whether a newer public GitHub Release exists.
``POST /update/install`` downloads that release's installer, launches it, and asks the app
to quit so the (UAC-gated) installer can replace the files.
"""

from __future__ import annotations

import threading

import httpx
from fastapi import APIRouter, Depends, Request
from starlette.applications import Starlette

from receipt_board import config
from receipt_board.api.deps import require_token
from receipt_board.api.errors import ApiError
from receipt_board.api.schemas import UpdateCheckResponse
from receipt_board.core import updates

update_router = APIRouter(tags=["update"], dependencies=[Depends(require_token)])

# Give the HTTP response time to flush before the window is destroyed.
SHUTDOWN_DELAY_SECONDS = 0.7


def schedule_shutdown(app: Starlette, *, delay: float | None = None) -> bool:
    """Fire ``app.state.shutdown_hook`` after a short delay (set by the GUI launcher).

    Returns whether a hook was scheduled (none is set under tests / headless runs).
    """
    hook = getattr(app.state, "shutdown_hook", None)
    if hook is None:
        return False
    timer = threading.Timer(SHUTDOWN_DELAY_SECONDS if delay is None else delay, hook)
    timer.daemon = True
    timer.start()
    return True


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


@update_router.post("/update/install")
def install_update(request: Request) -> dict:
    """Download the latest installer and launch it, then ask the app to quit.

    The asset URL is re-resolved server-side (never trusted from the client) and must be a
    GitHub host. This launches an interactive, UAC-gated installer — it does **not** install
    silently or without the user having confirmed in the GUI.
    """
    current = request.app.state.app_version
    try:
        with httpx.Client(timeout=updates.REQUEST_TIMEOUT, follow_redirects=True) as client:
            info = updates.check_for_update(current, client=client)
            if not info.update_available or not info.asset_url:
                raise ApiError(409, "no_update_available", "No newer installer is available")
            if not updates.is_trusted_asset_url(info.asset_url):
                raise ApiError(
                    400, "untrusted_asset", "Refusing to download from an untrusted host"
                )
            dest = updates.download_installer(
                info.asset_url, config.app_dir() / "updates", client=client
            )
    except httpx.HTTPError as exc:
        raise ApiError(502, "update_download_failed", "Could not download the installer") from exc

    updates.launch_installer(dest)
    schedule_shutdown(request.app)
    return {"launched": True, "version": info.latest, "installer": str(dest)}
